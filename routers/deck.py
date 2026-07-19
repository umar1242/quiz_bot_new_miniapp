"""
routers/deck.py
Флешкарты (колоды).

Создание:  awaiting_file → setup_title → сохранение
Обучение:  Anki-стиль — показ лица → «Показать ответ» → оборот → «Знаю / Не знаю».
           Карточки «Не знаю» возвращаются в конец очереди, пока не выучены.

Состояние сессии обучения держим в FSM (data["study"]) — без таблиц в БД,
т.к. это персональная практика без сохранения результатов.
"""
import asyncio
import html
import logging
import random

from aiogram import F, Router
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Document, Message, PollAnswer
from sqlalchemy.ext.asyncio import AsyncSession

from dto.quiz_dto import DeckCreateDTO, FlashcardDTO
from keyboards.deck_kb import (
    confirm_delete_deck_kb,
    deck_view_kb,
    decks_list_kb,
    study_done_kb,
    study_grade_kb,
    study_show_kb,
    tf_control_kb,
    tf_done_kb,
)
from config import settings
from services.flashcard_parser import parse_flashcards
from services.flashcard_service import create_deck, delete_deck, get_deck, get_user_decks
from utils.i18n import t
from utils.poll_utils import POLL_QUESTION_LIMIT

logger = logging.getLogger(__name__)

router = Router()

SUPPORTED = [".txt", ".docx", ".pdf"]

# Telegram: лимиты на пояснение к quiz poll
POLL_EXPLANATION_LIMIT = 200

# Сессии режима «Верно/Неверно» (в памяти, персональная практика без БД).
#   _tf_sessions:  user_id -> {chat_id, deck_id, title, statements, pos, correct, last_poll, lang, timer_sec}
#   _tf_poll_user: poll_id -> user_id  (маршрутизация ответа на нужную сессию)
#   _tf_timers:    user_id -> asyncio.Task (таймер текущего утверждения)
_tf_sessions: dict[int, dict] = {}
_tf_poll_user: dict[str, int] = {}
_tf_timers:   dict[int, asyncio.Task] = {}


def _cancel_tf_timer(user_id: int) -> None:
    task = _tf_timers.pop(user_id, None)
    if task and not task.done():
        task.cancel()


async def _tf_timer_expired(user_id: int, bot) -> None:
    """Таймер истёк — пользователь не ответил, переходим к следующему утверждению."""
    try:
        sess = _tf_sessions.get(user_id)
        if sess is None:
            return
        timer_sec = sess.get("timer_sec", settings.DEFAULT_TIMER_SEC)
        # Запоминаем позицию ДО сна, чтобы после сна проверить: не ответил ли уже пользователь
        expected_pos = sess["pos"]
        await asyncio.sleep(timer_sec)
        sess = _tf_sessions.get(user_id)
        if sess is None:
            return
        # Если pos сдвинулся — пользователь ответил, обработчик уже вызовет _send_tf_statement
        if sess["pos"] != expected_pos:
            return
        _tf_poll_user.pop(sess.get("last_poll", ""), None)
        sess["last_poll"] = None
        sess["pos"] += 1
        await _send_tf_statement(bot, user_id, sess["lang"])
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.exception("TF timer error user=%s: %s", user_id, e)
    finally:
        _tf_timers.pop(user_id, None)


class CreateDeck(StatesGroup):
    awaiting_file = State()
    setup_title   = State()


class StudyDeck(StatesGroup):
    studying = State()


# ---------------------------------------------------------------------------
# Список колод
# ---------------------------------------------------------------------------

async def _show_decks(message: Message, user_id: int, db: AsyncSession, lang: str, edit: bool = False) -> None:
    decks = await get_user_decks(db, user_id)
    if decks:
        text = t("deck.list_header", lang, count=len(decks))
    else:
        text = t("deck.list_empty", lang)
    kb = decks_list_kb(decks, lang)
    if edit:
        await message.edit_text(text, reply_markup=kb)
    else:
        await message.answer(text, reply_markup=kb)


@router.message(Command("flashcards"))
async def cmd_flashcards(message: Message, state: FSMContext, db: AsyncSession, lang: str) -> None:
    await state.clear()
    await _show_decks(message, message.from_user.id, db, lang)


@router.callback_query(F.data == "deck:list")
async def cb_deck_list(call: CallbackQuery, state: FSMContext, db: AsyncSession, lang: str) -> None:
    await state.clear()
    await _show_decks(call.message, call.from_user.id, db, lang, edit=True)
    await call.answer()


# ---------------------------------------------------------------------------
# Создание колоды
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "deck:create")
async def cb_deck_create(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.set_state(CreateDeck.awaiting_file)
    await call.message.answer(t("deck.ask_file", lang))
    await call.answer()


@router.message(CreateDeck.awaiting_file, F.document)
async def handle_deck_file(message: Message, state: FSMContext, lang: str) -> None:
    doc: Document = message.document
    ext = "." + doc.file_name.rsplit(".", 1)[-1].lower() if "." in doc.file_name else ""
    if ext not in SUPPORTED:
        await message.answer(
            t("creator.unsupported_format", lang, ext=ext, supported=", ".join(SUPPORTED))
        )
        return

    await message.answer(t("creator.processing", lang))

    bot = message.bot
    file = await bot.get_file(doc.file_id)
    buf = await bot.download_file(file.file_path)
    file_bytes = buf.read()

    try:
        cards = await parse_flashcards(doc.file_name, file_bytes)
    except ValueError as e:
        await message.answer(f"❌ {e}")
        return

    await message.answer(t("deck.parsed_ok", lang, count=len(cards)))

    cards_data = [{"front": c.front, "back": c.back, "back_false": c.back_false} for c in cards]
    suggested = doc.file_name.rsplit(".", 1)[0]
    await state.update_data(cards=cards_data, suggested_title=suggested)
    await state.set_state(CreateDeck.setup_title)
    await message.answer(t("deck.ask_title", lang, suggested=suggested))


@router.message(CreateDeck.awaiting_file)
async def handle_deck_file_wrong(message: Message, lang: str) -> None:
    await message.answer(t("deck.need_file", lang))


@router.message(CreateDeck.setup_title, F.text)
async def handle_deck_title(message: Message, state: FSMContext, db: AsyncSession, lang: str) -> None:
    data = await state.get_data()
    suggested = data.get("suggested_title", "Колода")

    raw = message.text.strip()
    title = suggested if raw == "." else raw

    if len(title) > 255:
        await message.answer(t("creator.title_too_long", lang, length=len(title)))
        return
    if not title:
        await message.answer(t("creator.title_empty", lang))
        return

    cards = [
        FlashcardDTO(front=c["front"], back=c["back"], back_false=c.get("back_false"))
        for c in data["cards"]
    ]
    await state.clear()

    deck = await create_deck(db, DeckCreateDTO(
        owner_id=message.from_user.id,
        title=title,
        cards=cards,
    ))

    await message.answer(
        t("deck.saved", lang, title=html.escape(deck.title), count=len(deck.cards)),
        reply_markup=deck_view_kb(deck.id, lang),
    )


# ---------------------------------------------------------------------------
# Просмотр / удаление колоды
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("deck:open:"))
async def cb_deck_open(call: CallbackQuery, state: FSMContext, db: AsyncSession, lang: str) -> None:
    await state.clear()
    deck_id = int(call.data.split(":")[2])
    deck = await get_deck(db, deck_id)
    if deck is None or deck.owner_id != call.from_user.id:
        await call.answer(t("deck.not_found", lang), show_alert=True)
        return

    await call.message.edit_text(
        t("deck.view", lang, title=html.escape(deck.title), count=len(deck.cards)),
        reply_markup=deck_view_kb(deck.id, lang),
    )
    await call.answer()


@router.callback_query(F.data.startswith("deck:delete:"))
async def cb_deck_delete(call: CallbackQuery, db: AsyncSession, lang: str) -> None:
    deck_id = int(call.data.split(":")[2])
    deck = await get_deck(db, deck_id)
    if deck is None or deck.owner_id != call.from_user.id:
        await call.answer(t("deck.not_found", lang), show_alert=True)
        return

    await call.message.edit_text(
        t("deck.confirm_delete", lang, title=html.escape(deck.title), count=len(deck.cards)),
        reply_markup=confirm_delete_deck_kb(deck.id, lang),
    )
    await call.answer()


@router.callback_query(F.data.startswith("deck:delete_yes:"))
async def cb_deck_delete_yes(call: CallbackQuery, db: AsyncSession, lang: str) -> None:
    deck_id = int(call.data.split(":")[2])
    ok = await delete_deck(db, deck_id, call.from_user.id)
    if not ok:
        await call.answer(t("deck.not_found", lang), show_alert=True)
        return
    await call.message.edit_text(t("deck.deleted", lang))
    await call.answer()


# ---------------------------------------------------------------------------
# Режим обучения
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("deck:share:"))
async def cb_deck_share(call: CallbackQuery, db: AsyncSession, lang: str) -> None:
    deck_id = int(call.data.split(":")[2])
    deck = await get_deck(db, deck_id)
    if deck is None or deck.owner_id != call.from_user.id:
        await call.answer(t("deck.not_found", lang), show_alert=True)
        return
    from utils.deeplink import make_deck_link
    link = make_deck_link(deck_id)
    await call.message.answer(
        t("deck.share_text", lang, title=deck.title, link=link)
    )
    await call.answer()


@router.callback_query(F.data.startswith("deck:study:"))
async def cb_deck_study(call: CallbackQuery, state: FSMContext, db: AsyncSession, lang: str) -> None:
    deck_id = int(call.data.split(":")[2])
    deck = await get_deck(db, deck_id)
    if deck is None:
        await call.answer(t("deck.not_found", lang), show_alert=True)
        return
    if not deck.cards:
        await call.answer(t("deck.empty", lang), show_alert=True)
        return

    cards = [{"front": c.front, "back": c.back, "back_false": c.back_false} for c in deck.cards]
    await state.set_state(StudyDeck.studying)
    await state.update_data(study={
        "deck_id": deck.id,
        "deck_title": deck.title,
        "cards": cards,
        "queue": list(range(len(cards))),   # индексы оставшихся карточек
        "total": len(cards),
        "again": 0,                          # сколько раз нажали «Не знаю»
    })
    await _render_front(call.message, state, lang)
    await call.answer()


async def _render_front(message: Message, state: FSMContext, lang: str) -> None:
    """Показывает лицевую сторону текущей карточки."""
    data = await state.get_data()
    study = data["study"]
    queue = study["queue"]

    if not queue:
        await _finish(message, state, lang)
        return

    card = study["cards"][queue[0]]
    learned = study["total"] - len(queue)
    text = t(
        "deck.card_front", lang,
        title=html.escape(study["deck_title"]),
        learned=learned, total=study["total"], remaining=len(queue),
        front=html.escape(card["front"]),
    )
    await message.edit_text(text, reply_markup=study_show_kb(lang))


@router.callback_query(StudyDeck.studying, F.data == "study:show")
async def cb_study_show(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    study = data["study"]
    queue = study["queue"]
    if not queue:
        await _finish(call.message, state, lang)
        await call.answer()
        return

    card = study["cards"][queue[0]]
    learned = study["total"] - len(queue)
    text = t(
        "deck.card_back", lang,
        title=html.escape(study["deck_title"]),
        learned=learned, total=study["total"], remaining=len(queue),
        front=html.escape(card["front"]),
        back=html.escape(card["back"]),
    )
    await call.message.edit_text(text, reply_markup=study_grade_kb(lang))
    await call.answer()


@router.callback_query(StudyDeck.studying, F.data == "study:know")
async def cb_study_know(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    study = data["study"]
    if study["queue"]:
        study["queue"].pop(0)   # карточка выучена — убираем из очереди
    await state.update_data(study=study)
    await _render_front(call.message, state, lang)
    await call.answer()


@router.callback_query(StudyDeck.studying, F.data == "study:dontknow")
async def cb_study_dontknow(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    study = data["study"]
    if study["queue"]:
        idx = study["queue"].pop(0)
        study["queue"].append(idx)   # возвращаем в конец — повторим позже
        study["again"] += 1
    await state.update_data(study=study)
    await _render_front(call.message, state, lang)
    await call.answer()


@router.callback_query(StudyDeck.studying, F.data == "study:stop")
async def cb_study_stop(call: CallbackQuery, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    study = data["study"]
    deck_id = study["deck_id"]
    learned = study["total"] - len(study["queue"])
    await state.clear()
    await call.message.edit_text(
        t("deck.stopped", lang, learned=learned, total=study["total"]),
        reply_markup=study_done_kb(deck_id, lang),
    )
    await call.answer()


async def _finish(message: Message, state: FSMContext, lang: str) -> None:
    """Все карточки выучены — показываем итог."""
    data = await state.get_data()
    study = data["study"]
    deck_id = study["deck_id"]
    total = study["total"]
    again = study["again"]
    await state.clear()
    await message.edit_text(
        t("deck.finished", lang, total=total, again=again),
        reply_markup=study_done_kb(deck_id, lang),
    )


# ---------------------------------------------------------------------------
# Режим «Верно / Неверно» (Telegram quiz poll)
# ---------------------------------------------------------------------------

def _build_tf_statements(cards: list[dict]) -> list[dict]:
    """
    Строит список утверждений из карточек (перемешанных).
    Для каждой карточки ~50/50: показать настоящий оборот или ложный.

    Ложный оборот берём из самой карточки (поле back_false), если автор его задал.
    Для старых карточек без ложного варианта — подменяем чужим оборотом
    из колоды (прежнее поведение, для обратной совместимости).
    """
    statements: list[dict] = []
    order = list(range(len(cards)))
    random.shuffle(order)

    for i in order:
        card = cards[i]
        real_back = card["back"]
        own_false = card.get("back_false")

        if own_false:
            # У карточки есть собственный ложный оборот — используем его
            if random.random() < 0.5:
                shown_back, is_real = real_back, True
            else:
                shown_back, is_real = own_false, False
        else:
            # Back-compat: подмена возможна только если есть карточка с другим оборотом
            others = [c["back"] for j, c in enumerate(cards) if j != i and c["back"] != real_back]
            if others and random.random() < 0.5:
                shown_back, is_real = random.choice(others), False
            else:
                shown_back, is_real = real_back, True

        statements.append({
            "front": card["front"],
            "back": shown_back,
            "is_real": is_real,
            "real_back": real_back,
        })
    return statements


def _drop_tf_session(user_id: int) -> dict | None:
    """Убирает сессию пользователя, её таймер и маршрут опроса. Возвращает старую сессию."""
    _cancel_tf_timer(user_id)
    sess = _tf_sessions.pop(user_id, None)
    if sess and sess.get("last_poll"):
        _tf_poll_user.pop(sess["last_poll"], None)
    return sess


@router.callback_query(F.data.startswith("deck:tf:"))
async def cb_deck_tf(call: CallbackQuery, state: FSMContext, db: AsyncSession, lang: str) -> None:
    deck_id = int(call.data.split(":")[2])
    deck = await get_deck(db, deck_id)
    if deck is None:
        await call.answer(t("deck.not_found", lang), show_alert=True)
        return
    if len(deck.cards) < 2:
        await call.answer(t("deck.tf_too_few", lang), show_alert=True)
        return

    await state.clear()
    _drop_tf_session(call.from_user.id)  # на случай незавершённого прошлого теста

    cards = [{"front": c.front, "back": c.back, "back_false": c.back_false} for c in deck.cards]
    statements = _build_tf_statements(cards)
    _tf_sessions[call.from_user.id] = {
        "chat_id": call.message.chat.id,
        "deck_id": deck.id,
        "title": deck.title,
        "statements": statements,
        "pos": 0,
        "correct": 0,
        "last_poll": None,
        "lang": lang,
        "timer_sec": settings.DEFAULT_TIMER_SEC,
        "plan_item_id": None,   # обычный запуск — без регистрации в плане
    }

    await call.message.answer(
        t("deck.tf_intro", lang, count=len(statements)),
        reply_markup=tf_control_kb(lang),
    )
    await _send_tf_statement(call.bot, call.from_user.id, lang)
    await call.answer()


async def launch_registered_tf(bot, db, chat_id, user, deck_id: int, plan_item_id: int, lang: str) -> None:
    """
    Запуск теста «Верно/Неверно» «с регистрацией» из планера.
    Результат засчитается в план ТОЛЬКО при полном прохождении (см. _finish_tf).
    """
    deck = await get_deck(db, deck_id)
    if deck is None:
        await bot.send_message(chat_id, t("deck.not_found", lang))
        return
    if len(deck.cards) < 2:
        await bot.send_message(chat_id, t("deck.tf_too_few", lang))
        return

    _drop_tf_session(user.id)
    cards = [{"front": c.front, "back": c.back, "back_false": c.back_false} for c in deck.cards]
    statements = _build_tf_statements(cards)
    _tf_sessions[user.id] = {
        "chat_id": chat_id,
        "deck_id": deck.id,
        "title": deck.title,
        "statements": statements,
        "pos": 0,
        "correct": 0,
        "last_poll": None,
        "lang": lang,
        "timer_sec": settings.DEFAULT_TIMER_SEC,
        "plan_item_id": plan_item_id,
    }
    await bot.send_message(
        chat_id,
        t("deck.tf_intro", lang, count=len(statements)),
        reply_markup=tf_control_kb(lang),
    )
    await _send_tf_statement(bot, user.id, lang)


async def _send_tf_statement(bot, user_id: int, lang: str) -> None:
    """Отправляет очередное утверждение как quiz poll, либо завершает тест."""
    sess = _tf_sessions.get(user_id)
    if sess is None:
        return

    pos = sess["pos"]
    statements = sess["statements"]
    if pos >= len(statements):
        await _finish_tf(bot, user_id, lang)
        return

    st = statements[pos]
    chat_id = sess["chat_id"]
    correct_id = 0 if st["is_real"] else 1
    ask = t("deck.tf_ask", lang)

    # Текст опроса — plain text (poll не парсит HTML). Если длинно — выносим пару
    # в отдельное сообщение, а в опросе оставляем короткий вопрос.
    prefix = f"[{pos + 1}/{len(statements)}] "
    pair = f"🔬 {st['front']}\n\n📝 {st['back']}"
    full_q = f"{prefix}{pair}\n\n{ask}"
    if len(full_q) <= POLL_QUESTION_LIMIT:
        question_text = full_q
    else:
        await bot.send_message(
            chat_id,
            f"🔬 <b>{html.escape(st['front'])}</b>\n\n📝 {html.escape(st['back'])}",
        )
        question_text = f"{prefix}{ask}"

    if st["is_real"]:
        explanation = t("deck.tf_expl_true", lang)
    else:
        explanation = t("deck.tf_expl_false", lang, real=st["real_back"])
    explanation = explanation[:POLL_EXPLANATION_LIMIT]

    timer_sec = sess.get("timer_sec", settings.DEFAULT_TIMER_SEC)
    poll_msg = await bot.send_poll(
        chat_id=chat_id,
        question=question_text,
        options=[t("deck.tf_true", lang), t("deck.tf_false", lang)],
        type="quiz",
        correct_option_id=correct_id,
        is_anonymous=False,
        explanation=explanation,
        open_period=max(5, min(timer_sec, 600)) if timer_sec > 0 else None,
    )

    sess["last_poll"] = poll_msg.poll.id
    _tf_poll_user[poll_msg.poll.id] = user_id

    # Запускаем asyncio-таймер — если пользователь не ответит, переходим сами
    _cancel_tf_timer(user_id)
    if timer_sec > 0:
        task = asyncio.create_task(_tf_timer_expired(user_id, bot))
        _tf_timers[user_id] = task


@router.poll_answer()
async def on_tf_poll_answer(poll_answer: PollAnswer, bot, lang: str) -> None:
    """Ответ на quiz poll режима «Верно/Неверно». Чужие поллы пропускаем дальше."""
    user_id = _tf_poll_user.get(poll_answer.poll_id)
    if user_id is None:
        # Это не наш поллл (например, обычный квиз) — пусть обработают другие роутеры
        raise SkipHandler()

    _cancel_tf_timer(user_id)
    _tf_poll_user.pop(poll_answer.poll_id, None)
    sess = _tf_sessions.get(user_id)
    if sess is None:
        return

    answered_pos = sess["pos"]
    st = sess["statements"][answered_pos]
    correct_id = 0 if st["is_real"] else 1
    chosen = poll_answer.option_ids[0] if poll_answer.option_ids else None
    if chosen == correct_id:
        sess["correct"] += 1
    sess["pos"] += 1
    sess["last_poll"] = None  # сигнал таймеру: вопрос уже отвечён

    await asyncio.sleep(1)  # даём увидеть правильный ответ перед следующим

    # Перепроверяем сессию после sleep — таймер мог успеть сдвинуть pos ещё раз
    sess = _tf_sessions.get(user_id)
    if sess is None or sess["pos"] != answered_pos + 1:
        return
    await _send_tf_statement(bot, user_id, lang)


@router.callback_query(F.data == "tf:stop")
async def cb_tf_stop(call: CallbackQuery, lang: str) -> None:
    sess = _drop_tf_session(call.from_user.id)
    if sess is None:
        await call.message.edit_text(t("deck.tf_stopped_none", lang))
    else:
        await call.message.edit_text(
            t("deck.tf_stopped", lang, correct=sess["correct"], total=len(sess["statements"])),
            reply_markup=tf_done_kb(sess["deck_id"], lang),
        )
    await call.answer()


async def _finish_tf(bot, user_id: int, lang: str) -> None:
    """Все утверждения пройдены — показываем итог."""
    sess = _drop_tf_session(user_id)
    if sess is None:
        return
    # Планер: засчитываем ТОЛЬКО если тест запущен «с регистрацией» из планера
    # И пройден до конца (мы здесь). Остановка на середине не регистрируется.
    if sess.get("plan_item_id"):
        from services.planner_service import log_registered_event_standalone
        from db.models import StudyKind
        await log_registered_event_standalone(
            user_id, sess["plan_item_id"], StudyKind.tf, sess["deck_id"],
            correct=sess["correct"], total=len(sess["statements"]),
        )
    await bot.send_message(
        sess["chat_id"],
        t("deck.tf_finished", lang, correct=sess["correct"], total=len(sess["statements"])),
        reply_markup=tf_done_kb(sess["deck_id"], lang),
    )
