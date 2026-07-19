"""
routers/edit.py
Редактирование квиза создателем + меню просмотра квиза (view:* callbacks).
"""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.edit_kb import (
    confirm_delete_quiz_kb,
    edit_timer_kb,
    question_list_kb,
    quiz_edit_menu_kb,
    quiz_view_kb,
)
from services.quiz_service import (
    delete_question,
    delete_quiz,
    get_quiz,
    replace_question,
    update_quiz_settings,
)
from services.stats_service import get_quiz_respondents_count
from utils.deeplink import make_group_quiz_link, make_quiz_link
from utils.formatters import fmt_quiz_info, fmt_time
from utils.validators import validate_questions
from utils.i18n import t
from dto.quiz_dto import QuestionDTO, AnswerDTO

router = Router()


class EditQuiz(StatesGroup):
    awaiting_new_question = State()
    _editing_question_id  = State()


# ---------------------------------------------------------------------------
# /quiz_X — открыть меню квиза
# ---------------------------------------------------------------------------

@router.message(F.text.startswith("/quiz_"))
async def cmd_quiz_edit(message: Message, db: AsyncSession, lang: str) -> None:
    """
    Команда вида /quiz_42 — открывает меню управления квизом.
    """
    raw = message.text.lstrip("/quiz_")
    try:
        quiz_id = int(raw)
    except ValueError:
        return

    quiz = await get_quiz(db, quiz_id)
    if quiz is None or quiz.owner_id != message.from_user.id:
        await message.answer(t("common.quiz_not_found", lang))
        return

    link = make_quiz_link(quiz_id)
    respondents = await get_quiz_respondents_count(db, quiz_id)

    text = t("view.quiz_menu", lang,
             title=quiz.title, count=len(quiz.questions),
             timer=quiz.timer_sec, respondents=respondents, link=link)
    await message.answer(text, reply_markup=quiz_view_kb(quiz, lang))


# ---------------------------------------------------------------------------
# view:solo — Пройти тест (ссылка для прохождения)
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("view:solo:"))
async def cb_view_solo(call: CallbackQuery, db: AsyncSession, lang: str) -> None:
    quiz_id = int(call.data.split(":")[2])
    link = make_quiz_link(quiz_id)
    await call.answer()
    await call.message.answer(t("view.solo_link", lang, link=link))


# ---------------------------------------------------------------------------
# view:group — Решать в группе
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("view:group:"))
async def cb_view_group(call: CallbackQuery, db: AsyncSession, lang: str) -> None:
    quiz_id = int(call.data.split(":")[2])
    link = make_group_quiz_link(quiz_id)
    await call.answer()
    await call.message.answer(t("view.group_instr", lang, link=link))


# ---------------------------------------------------------------------------
# view:share — Поделиться
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("view:share:"))
async def cb_view_share(call: CallbackQuery, db: AsyncSession, lang: str) -> None:
    quiz_id = int(call.data.split(":")[2])
    quiz = await get_quiz(db, quiz_id)
    link = make_quiz_link(quiz_id)
    await call.answer()
    await call.message.answer(t("view.share", lang, title=quiz.title, link=link))


# ---------------------------------------------------------------------------
# view:stats — Статистика
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("view:stats:"))
async def cb_view_stats(call: CallbackQuery, db: AsyncSession, lang: str) -> None:
    quiz_id = int(call.data.split(":")[2])
    quiz = await get_quiz(db, quiz_id)
    if quiz is None:
        await call.answer(t("common.quiz_not_found", lang), show_alert=True)
        return

    respondents = await get_quiz_respondents_count(db, quiz_id)
    await call.answer()
    await call.message.answer(
        t("view.stats", lang, title=quiz.title, count=len(quiz.questions), respondents=respondents)
    )


# ---------------------------------------------------------------------------
# view:edit — войти в подменю редактирования
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("view:edit:"))
async def cb_view_edit(call: CallbackQuery, db: AsyncSession, lang: str) -> None:
    quiz_id = int(call.data.split(":")[2])
    quiz = await get_quiz(db, quiz_id)
    if quiz is None or quiz.owner_id != call.from_user.id:
        await call.answer(t("common.quiz_not_found", lang), show_alert=True)
        return

    link = make_quiz_link(quiz_id)
    await call.message.edit_text(
        fmt_quiz_info(quiz, link, lang),
        reply_markup=quiz_edit_menu_kb(quiz, lang),
    )


# ---------------------------------------------------------------------------
# Изменить таймер
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("edit:timer:"))
async def cb_edit_timer(call: CallbackQuery, lang: str) -> None:
    quiz_id = int(call.data.split(":")[2])
    await call.message.edit_text(
        t("edit.choose_timer", lang),
        reply_markup=edit_timer_kb(quiz_id, lang),
    )


@router.callback_query(F.data.startswith("edit_timer:"))
async def cb_set_timer(call: CallbackQuery, db: AsyncSession, lang: str) -> None:
    _, quiz_id_str, sec_str = call.data.split(":")
    quiz_id, timer_sec = int(quiz_id_str), int(sec_str)

    quiz = await update_quiz_settings(db, quiz_id, call.from_user.id, timer_sec=timer_sec)
    if quiz is None:
        await call.answer(t("common.quiz_not_found", lang), show_alert=True)
        return

    label = fmt_time(timer_sec, lang)
    await call.answer(t("edit.timer_updated", lang, label=label), show_alert=False)
    link = make_quiz_link(quiz_id)
    await call.message.edit_text(fmt_quiz_info(quiz, link, lang), reply_markup=quiz_edit_menu_kb(quiz, lang))


# ---------------------------------------------------------------------------
# Переключить shuffle_q / shuffle_a
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("edit:shuffle_q:"))
async def cb_toggle_shuffle_q(call: CallbackQuery, db: AsyncSession, lang: str) -> None:
    quiz_id = int(call.data.split(":")[2])
    quiz = await get_quiz(db, quiz_id)
    if quiz is None or quiz.owner_id != call.from_user.id:
        await call.answer(t("common.quiz_not_found", lang), show_alert=True)
        return

    quiz = await update_quiz_settings(db, quiz_id, call.from_user.id, shuffle_q=not quiz.shuffle_q)
    link = make_quiz_link(quiz_id)
    await call.message.edit_text(fmt_quiz_info(quiz, link, lang), reply_markup=quiz_edit_menu_kb(quiz, lang))


@router.callback_query(F.data.startswith("edit:shuffle_a:"))
async def cb_toggle_shuffle_a(call: CallbackQuery, db: AsyncSession, lang: str) -> None:
    quiz_id = int(call.data.split(":")[2])
    quiz = await get_quiz(db, quiz_id)
    if quiz is None or quiz.owner_id != call.from_user.id:
        await call.answer(t("common.quiz_not_found", lang), show_alert=True)
        return

    quiz = await update_quiz_settings(db, quiz_id, call.from_user.id, shuffle_a=not quiz.shuffle_a)
    link = make_quiz_link(quiz_id)
    await call.message.edit_text(fmt_quiz_info(quiz, link, lang), reply_markup=quiz_edit_menu_kb(quiz, lang))


# ---------------------------------------------------------------------------
# Удалить вопрос
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("edit:delete_q:"))
async def cb_delete_question_choose(call: CallbackQuery, db: AsyncSession, lang: str) -> None:
    quiz_id = int(call.data.split(":")[2])
    quiz = await get_quiz(db, quiz_id)
    if quiz is None or quiz.owner_id != call.from_user.id:
        await call.answer(t("common.quiz_not_found", lang), show_alert=True)
        return

    if len(quiz.questions) <= 1:
        await call.answer(t("edit.cant_delete_last", lang), show_alert=True)
        return

    await call.message.edit_text(
        t("edit.choose_q_delete", lang),
        reply_markup=question_list_kb(quiz, action="delete", lang=lang),
    )


@router.callback_query(F.data.startswith("qaction:delete:"))
async def cb_delete_question_confirm(call: CallbackQuery, db: AsyncSession, lang: str) -> None:
    question_id = int(call.data.split(":")[2])
    deleted = await delete_question(db, question_id, call.from_user.id)
    if not deleted:
        await call.answer(t("edit.q_not_found", lang), show_alert=True)
        return

    await call.answer(t("edit.q_deleted_alert", lang), show_alert=False)
    await call.message.edit_text(t("edit.q_deleted", lang))


# ---------------------------------------------------------------------------
# Заменить вопрос
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("edit:replace_q:"))
async def cb_replace_question_choose(call: CallbackQuery, db: AsyncSession, lang: str) -> None:
    quiz_id = int(call.data.split(":")[2])
    quiz = await get_quiz(db, quiz_id)
    if quiz is None or quiz.owner_id != call.from_user.id:
        await call.answer(t("common.quiz_not_found", lang), show_alert=True)
        return

    await call.message.edit_text(
        t("edit.choose_q_replace", lang),
        reply_markup=question_list_kb(quiz, action="replace", lang=lang),
    )


@router.callback_query(F.data.startswith("qaction:replace:"))
async def cb_replace_question_enter_fsm(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    question_id = int(call.data.split(":")[2])
    await state.set_state(EditQuiz.awaiting_new_question)
    await state.update_data(replacing_question_id=question_id)
    await call.message.edit_text(t("edit.replace_prompt", lang))


@router.message(EditQuiz.awaiting_new_question)
async def handle_new_question_text(message: Message, state: FSMContext, db: AsyncSession, lang: str) -> None:
    data = await state.get_data()
    question_id = data.get("replacing_question_id")
    if question_id is None:
        await state.clear()
        return

    from services.parser.base import ANSWER_SEP, ANSWER_SEP_INLINE, CORRECT_MARK

    text = message.text.replace('\r\n', '\n').replace('\r', '\n').strip()
    # Сначала пробуем классический формат (= на отдельных строках),
    # затем inline-вариант HEMIS (= прямо в тексте).
    parts = [p.strip() for p in ANSWER_SEP.split(text) if p.strip()]
    if len(parts) < 3:
        parts = [p.strip() for p in ANSWER_SEP_INLINE.split(text) if p.strip()]

    if len(parts) < 3:
        await message.answer(t("edit.replace_bad_format", lang))
        return

    question_text = parts[0]
    answers = []
    for raw in parts[1:]:
        is_correct = raw.startswith(CORRECT_MARK)
        answer_text = raw.lstrip(CORRECT_MARK).strip()
        if answer_text:
            answers.append(AnswerDTO(text=answer_text, is_correct=is_correct))

    new_dto = QuestionDTO(text=question_text, answers=answers)

    errors = validate_questions([new_dto], lang)
    if errors:
        await message.answer("❌ " + "\n".join(errors))
        return

    updated = await replace_question(db, question_id, message.from_user.id, new_dto)
    await state.clear()

    if updated is None:
        await message.answer(t("edit.q_not_found_or_no_rights", lang))
        return

    await message.answer(
        t("edit.q_replaced", lang, text=updated.text)
        + "\n".join(
            f"{'✅' if a.is_correct else '▪️'} {a.text}"
            for a in updated.answers
        )
    )


# ---------------------------------------------------------------------------
# Удалить весь квиз
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("edit:delete_quiz:"))
async def cb_delete_quiz_confirm(call: CallbackQuery, db: AsyncSession, lang: str) -> None:
    quiz_id = int(call.data.split(":")[2])
    quiz = await get_quiz(db, quiz_id)
    title = quiz.title if quiz else t("edit.untitled", lang)
    await call.message.edit_text(
        t("edit.confirm_delete_quiz", lang,
          title=title, count=len(quiz.questions) if quiz else "?"),
        reply_markup=confirm_delete_quiz_kb(quiz_id, lang),
    )


@router.callback_query(F.data.startswith("confirm_delete:"))
async def cb_delete_quiz_execute(call: CallbackQuery, db: AsyncSession, lang: str) -> None:
    quiz_id = int(call.data.split(":")[1])
    deleted = await delete_quiz(db, quiz_id, call.from_user.id)
    if deleted:
        await call.message.edit_text(t("edit.quiz_deleted", lang))
    else:
        await call.answer(t("common.quiz_not_found", lang), show_alert=True)


# ---------------------------------------------------------------------------
# Навигация — Назад (из подменю редактирования → меню просмотра)
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("edit:back_menu:"))
async def cb_back_to_menu(call: CallbackQuery, db: AsyncSession, lang: str) -> None:
    quiz_id = int(call.data.split(":")[2])
    quiz = await get_quiz(db, quiz_id)
    if quiz is None:
        await call.message.edit_text(t("common.quiz_not_found", lang))
        return
    link = make_quiz_link(quiz_id)
    # Возвращаемся на главное меню квиза (view), не в edit
    respondents = await get_quiz_respondents_count(db, quiz_id)
    text = t("view.quiz_menu", lang,
             title=quiz.title, count=len(quiz.questions),
             timer=quiz.timer_sec, respondents=respondents, link=link)
    await call.message.edit_text(text, reply_markup=quiz_view_kb(quiz, lang))


@router.callback_query(F.data == "edit:back")
async def cb_back(call: CallbackQuery, lang: str) -> None:
    await call.message.edit_text(t("common.use_start", lang))
