"""
routers/start.py
Обработка /start, /myquiz, /help, /settings — обычный вход и deep link (запуск квиза по ссылке).
Также — выбор и смена языка интерфейса.
"""
import html

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy.ext.asyncio import AsyncSession

from services.quiz_service import get_quiz, get_user_quizzes
from services.session_service import create_solo_session, create_group_session, get_active_session_by_chat
from services.timer_service import save_question_order, save_poll_session
from services.user_service import get_lang_raw, set_lang, get_lang
from redis_client import acquire_quiz_lock, release_quiz_lock
from services.quiz_service import get_ordered_questions, get_ordered_answers
from services.stats_service import get_quiz_respondents_count, get_respondents_batch
from utils.deeplink import (
    make_deck_link,
    make_quiz_link,
    parse_deck_start_param,
    parse_plan_item_param,
    parse_start_param,
)
from utils.formatters import fmt_quiz_info, group_quizzes, fmt_quiz_list_grouped
from utils.poll_utils import build_poll_data, maybe_send_long_question
from utils.i18n import t, LANG_NAMES
from keyboards.group_kb import join_kb
from keyboards.edit_kb import quiz_view_kb, myquiz_list_kb
from keyboards.settings_kb import language_kb, settings_kb
from db.models import SessionMode

router = Router()


async def _show_main_menu(message: Message, user_id: int, db: AsyncSession, lang: str) -> None:
    """Главное меню — приветствие + список квизов. message используется только для .answer()."""
    quizzes = await get_user_quizzes(db, user_id)
    respondents = await get_respondents_batch(db, [q.id for q in quizzes])
    groups = group_quizzes(quizzes)
    text = t("start.welcome", lang) + fmt_quiz_list_grouped(groups, respondents, page=0, lang=lang)
    await message.answer(text, reply_markup=myquiz_list_kb(groups, page=0, lang=lang))


@router.message(CommandStart())
async def cmd_start(message: Message, db: AsyncSession, lang: str, bot) -> None:
    args = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""

    # --- Deep link: запуск задания плана «с регистрацией» ---
    plan_item_id = parse_plan_item_param(args)
    if plan_item_id is not None:
        await _prompt_registration(message, db, plan_item_id)
        return

    quiz_id = parse_start_param(args)
    deck_id = parse_deck_start_param(args)

    # --- Deep link: открыть колоду ---
    if deck_id is not None:
        from services.flashcard_service import get_deck
        from keyboards.deck_kb import deck_view_kb, deck_shared_view_kb
        deck = await get_deck(db, deck_id)
        if deck is None:
            await message.answer(t("deck.not_found", lang))
            return
        is_owner = deck.owner_id == message.from_user.id
        kb = deck_view_kb(deck.id, lang) if is_owner else deck_shared_view_kb(deck.id, lang)
        await message.answer(
            t("deck.open_via_link", lang, title=deck.title, count=len(deck.cards)),
            reply_markup=kb,
        )
        return

    # --- Обычный /start без параметра ---
    if quiz_id is None:
        # Если пользователь ещё не выбирал язык — показываем выбор языка
        saved = await get_lang_raw(db, message.from_user.id)
        if saved is None:
            await message.answer(t("lang.choose", lang), reply_markup=language_kb("setlang"))
            return
        await _show_main_menu(message, message.from_user.id, db, lang)
        return

    # --- Deep link: запуск квиза ---
    quiz = await get_quiz(db, quiz_id)
    if quiz is None:
        await message.answer(t("common.quiz_not_found_deleted", lang))
        return

    existing = await get_active_session_by_chat(db, message.chat.id)
    if existing:
        await message.answer(t("start.chat_busy", lang))
        return

    # Лок — защита от двойного запуска если два пользователя нажали ссылку одновременно
    if not await acquire_quiz_lock(quiz_id):
        await message.answer(t("start.quiz_launching", lang))
        return

    is_group = message.chat.type in ("group", "supergroup")

    try:
        if is_group:
            session = await create_group_session(db, quiz_id, message.chat.id)
            await message.answer(
                t("start.group_announce", lang,
                  title=quiz.title, count=len(quiz.questions), timer=quiz.timer_sec),
                reply_markup=join_kb(session.id, lang),
            )
        else:
            session = await create_solo_session(
                db, quiz_id, message.chat.id,
                message.from_user.id, message.from_user.username
            )
            questions = get_ordered_questions(quiz)
            await save_question_order(session.id, [q.id for q in questions])
            await _send_question(
            message.chat.id, session.id, questions[0],
            quiz.timer_sec, quiz.shuffle_a, bot,
            question_num=1, total=len(questions), lang=lang,
        )
    finally:
        await release_quiz_lock(quiz_id)


# ---------------------------------------------------------------------------
# Выбор / смена языка
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("setlang:"))
async def cb_set_language_first(call: CallbackQuery, db: AsyncSession) -> None:
    """Первый выбор языка при /start."""
    chosen = call.data.split(":")[1]
    await set_lang(db, call.from_user.id, chosen)
    await call.answer(t("lang.changed", chosen))
    # Показываем главное меню на выбранном языке
    await call.message.edit_text(t("lang.changed", chosen))
    await _show_main_menu(call.message, call.from_user.id, db, chosen)


@router.callback_query(F.data.startswith("chlang:"))
async def cb_change_language(call: CallbackQuery, db: AsyncSession) -> None:
    """Смена языка из настроек."""
    chosen = call.data.split(":")[1]
    await set_lang(db, call.from_user.id, chosen)
    await call.answer(t("lang.changed", chosen))
    await call.message.edit_text(
        t("settings.title", chosen, lang_name=LANG_NAMES[chosen]),
        reply_markup=settings_kb(chosen),
    )


@router.message(Command("settings"))
async def cmd_settings(message: Message, db: AsyncSession, lang: str) -> None:
    """Меню настроек."""
    await message.answer(
        t("settings.title", lang, lang_name=LANG_NAMES[lang]),
        reply_markup=settings_kb(lang),
    )


@router.callback_query(F.data == "settings:lang")
async def cb_settings_language(call: CallbackQuery, lang: str) -> None:
    """Открыть выбор языка из настроек."""
    await call.message.edit_text(t("lang.choose", lang), reply_markup=language_kb("chlang"))
    await call.answer()


@router.message(Command("myquiz"))
async def cmd_myquiz(message: Message, db: AsyncSession, lang: str) -> None:
    """Список квизов пользователя с кнопками."""
    quizzes = await get_user_quizzes(db, message.from_user.id)

    if not quizzes:
        await message.answer(t("start.no_quizzes", lang))
        return

    respondents = await get_respondents_batch(db, [q.id for q in quizzes])
    groups = group_quizzes(quizzes)
    text = fmt_quiz_list_grouped(groups, respondents, page=0, lang=lang)
    await message.answer(text, reply_markup=myquiz_list_kb(groups, page=0, lang=lang))


@router.callback_query(F.data.startswith("myquiz:open:"))
async def cb_myquiz_open(call: CallbackQuery, db: AsyncSession, lang: str) -> None:
    """Открыть меню квиза из списка /myquiz."""
    quiz_id = int(call.data.split(":")[2])
    quiz = await get_quiz(db, quiz_id)
    if quiz is None or quiz.owner_id != call.from_user.id:
        await call.answer(t("common.quiz_not_found", lang), show_alert=True)
        return

    link = make_quiz_link(quiz_id)
    await call.message.answer(fmt_quiz_info(quiz, link, lang), reply_markup=quiz_view_kb(quiz, lang))
    await call.answer()



@router.callback_query(F.data.startswith("myquiz:page:"))
async def cb_myquiz_page(call: CallbackQuery, db: AsyncSession, lang: str) -> None:
    """Переключение страницы в /myquiz."""
    page = int(call.data.split(":")[2])
    quizzes = await get_user_quizzes(db, call.from_user.id)
    respondents = await get_respondents_batch(db, [q.id for q in quizzes])
    groups = group_quizzes(quizzes)
    text = fmt_quiz_list_grouped(groups, respondents, page=page, lang=lang)
    await call.message.edit_text(text, reply_markup=myquiz_list_kb(groups, page=page, lang=lang))
    await call.answer()


@router.callback_query(F.data.startswith("myquiz:group:"))
async def cb_myquiz_group(call: CallbackQuery, db: AsyncSession, lang: str) -> None:
    """Раскрывает список частей внутри группы."""
    # callback_data: myquiz:group:PAGE:GLOBAL_IDX
    parts = call.data.split(":")
    back_page  = int(parts[2])
    group_idx  = int(parts[3])

    quizzes = await get_user_quizzes(db, call.from_user.id)
    respondents = await get_respondents_batch(db, [q.id for q in quizzes])

    from utils.formatters import fmt_time, group_quizzes as _group_quizzes
    all_groups = _group_quizzes(quizzes)

    if group_idx >= len(all_groups):
        await call.answer(t("common.quiz_not_found", lang), show_alert=True)
        return

    g = all_groups[group_idx]
    base_title = g["base"]
    group_quizzes_list = g["quizzes"]

    lines = [f"📦 <b>{base_title}</b>  — {t('fmt.parts_count', lang, n=len(group_quizzes_list))}\n"]
    for i, q in enumerate(group_quizzes_list, start=1):
        count = respondents.get(q.id, 0)
        resp = t("fmt.respondents", lang, count=count) if count else ""
        lines.append(
            f"{i}. <b>{q.title}</b>{resp}\n"
            + t("fmt.single_line", lang, count=len(q.questions),
                timer=fmt_time(q.timer_sec, lang),
                shuffle_a=(t('fmt.all', lang) if q.shuffle_a else t('fmt.in_order', lang))) + "\n"
            + f"   /quiz_{q.id}"
        )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    back_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t("common.back", lang), callback_data=f"myquiz:page:{back_page}")
    ]])

    await call.message.edit_text("\n\n".join(lines), reply_markup=back_kb)
    await call.answer()


@router.message(Command("help"))
async def cmd_help(message: Message, lang: str) -> None:
    """Справка по боту."""
    await message.answer(t("help.text", lang))


async def _send_question(
    chat_id: int, session_id: int, question,
    timer_sec: int, shuffle_a: bool, bot,
    question_num: int = 1, total: int = 1, lang: str = "ru",
) -> None:
    """Отправляет один вопрос как Telegram Quiz Poll."""
    from services.timer_service import start_question_timer
    from routers.quiz_solo import _next_question

    answers = get_ordered_answers(question, shuffle_a)
    correct_idx = next(i for i, a in enumerate(answers) if a.is_correct)
    question_text, options = build_poll_data(question, answers)

    await maybe_send_long_question(chat_id, question, answers, bot)
    await bot.send_message(chat_id, t("start.progress", lang, num=question_num, total=total))

    poll_msg = await bot.send_poll(
        chat_id=chat_id,
        question=question_text,
        options=options,
        type="quiz",
        correct_option_id=correct_idx,
        is_anonymous=False,
        open_period=max(5, min(timer_sec, 600)) if timer_sec > 0 else None,
        explanation=question.explanation[:200] if question.explanation else None,
    )

    await save_poll_session(
        poll_msg.poll.id,
        session_id,
        question.id,
        answer_ids=[a.id for a in answers],
        ttl=timer_sec + 60,
    )
    await start_question_timer(
        session_id, question.id, timer_sec,
        lambda sid, b, qid=question.id: _next_question(sid, b, from_question_id=qid),
        bot,
    )


# ---------------------------------------------------------------------------
# Планер: регистрируемый запуск задания (deep link pi_<item_id>)
# ---------------------------------------------------------------------------

async def _prompt_registration(message: Message, db: AsyncSession, item_id: int) -> None:
    """Показывает условия регистрации перед запуском задания из планера."""
    from services.planner_service import get_plan_item
    item = await get_plan_item(db, message.from_user.id, item_id)
    if item is None:
        await message.answer(
            "❌ Задание плана не найдено или устарело.\n"
            "Открой планер (кнопка 📊 в меню) и создай план заново."
        )
        return
    mode = "тест «Верно/Неверно» по колоде" if item.kind == "tf" else "квиз"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Начать (с регистрацией)",
                              callback_data=f"plreg:start:{item.id}")],
        [InlineKeyboardButton(text="✖️ Отмена", callback_data="plreg:cancel")],
    ])
    await message.answer(
        "📋 <b>Регистрация в плане</b>\n\n"
        f"Задание: <b>{html.escape(item.title)}</b> — {mode}.\n\n"
        "⚠️ <b>Условие:</b> прохождение зачтётся в план, <b>только если дойдёшь до конца</b>. "
        "Нажмёшь «Стоп» или выйдешь на середине — не засчитается.\n\n"
        "Готов начать?",
        reply_markup=kb,
    )


async def launch_registered_quiz(bot, db: AsyncSession, chat_id: int, user,
                                 quiz_id: int, plan_item_id: int, lang: str) -> None:
    """Запуск solo-квиза «с регистрацией» из планера (см. _prompt_registration)."""
    quiz = await get_quiz(db, quiz_id)
    if quiz is None:
        await bot.send_message(chat_id, t("common.quiz_not_found_deleted", lang))
        return
    existing = await get_active_session_by_chat(db, chat_id)
    if existing:
        await bot.send_message(chat_id, t("start.chat_busy", lang))
        return
    if not await acquire_quiz_lock(quiz_id):
        await bot.send_message(chat_id, t("start.quiz_launching", lang))
        return
    try:
        session = await create_solo_session(
            db, quiz_id, chat_id, user.id, user.username, plan_item_id=plan_item_id
        )
        questions = get_ordered_questions(quiz)
        await save_question_order(session.id, [q.id for q in questions])
        await _send_question(
            chat_id, session.id, questions[0],
            quiz.timer_sec, quiz.shuffle_a, bot,
            question_num=1, total=len(questions), lang=lang,
        )
    finally:
        await release_quiz_lock(quiz_id)
