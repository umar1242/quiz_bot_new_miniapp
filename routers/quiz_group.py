"""
routers/quiz_group.py
Групповой режим.
"""
import asyncio
import logging

from aiogram import F, Router
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.filters import Command
from aiogram.types import CallbackQuery, PollAnswer, Message

from db.base import AsyncSessionFactory
from db.models import SessionMode, SessionStatus
from keyboards.group_kb import join_kb, joined_kb
from redis_client import RedisKeys, sadd_member, scard, smembers, acquire_quiz_lock, release_quiz_lock
from services.quiz_service import get_ordered_answers
from services.response_service import record_response, already_answered, record_skipped_responses
from services.session_service import (
    add_participant, get_session, get_participants,
    start_group_session, advance_question, finish_session,
    build_question_order, get_active_session_by_chat,
)
from services.stats_service import get_group_stats, get_group_question_stats
from services.user_service import get_lang
from services.timer_service import (
    get_poll_session, get_question_order,
    save_poll_session, save_question_order, start_question_timer,
    cancel_timer, get_session_lock,
)
from utils.formatters import fmt_group_results, fmt_group_results_detailed
from utils.i18n import t
from keyboards.edit_kb import export_group_kb
from utils.poll_utils import build_poll_data, maybe_send_long_question

logger = logging.getLogger(__name__)
router = Router()

# ---------------------------------------------------------------------------
# Запуск квиза прямо из объявления (inline → кнопка "🚀 Начать квиз")
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("group_start_from_announce:"))
async def cb_group_start_from_announce(call: CallbackQuery, lang: str) -> None:
    """
    Срабатывает когда пользователь нажимает '🚀 Начать квиз' в объявлении.
    Создаёт групповую сессию в текущей группе и публикует объявление с кнопками
    'Присоединиться' / 'Начать (только создатель)'.
    """
    # Работает только в группах
    if call.message.chat.type not in ("group", "supergroup"):
        await call.answer(t("quiz.only_in_groups", lang), show_alert=True)
        return

    quiz_id = int(call.data.split(":")[1])

    # Лок — защита от двойного нажатия кнопки
    if not await acquire_quiz_lock(quiz_id):
        await call.answer(t("start.quiz_launching", lang), show_alert=True)
        return

    try:
        async with AsyncSessionFactory() as db:
            async with db.begin():
                from services.quiz_service import get_quiz
                quiz = await get_quiz(db, quiz_id)

                if quiz is None:
                    await call.answer(t("common.quiz_not_found_deleted", lang), show_alert=True)
                    return

                existing = await get_active_session_by_chat(db, call.message.chat.id)
                if existing:
                    await call.answer(t("quiz.group_busy", lang), show_alert=True)
                    return

                # Создаём групповую сессию
                from services.session_service import create_group_session
                session = await create_group_session(db, quiz_id, call.message.chat.id)
    finally:
        await release_quiz_lock(quiz_id)

    await call.answer()

    # Редактируем объявление — убираем кнопку "Начать квиз", добавляем "Присоединиться"
    await call.message.edit_text(
        t("start.group_announce", lang,
          title=quiz.title, count=len(quiz.questions), timer=quiz.timer_sec),
        reply_markup=join_kb(session.id, lang),
    )




@router.message(Command("stop", ignore_mention=True), F.chat.type.in_({"group", "supergroup"}))
async def cmd_stop_group(message: Message, db, lang: str) -> None:
    """Останавливает групповой квиз. Только создатель квиза может остановить."""

    session = await get_active_session_by_chat(db, message.chat.id)

    if session is None:
        await message.answer(t("quiz.no_active", lang))
        return

    if session.mode != SessionMode.group:
        return

    # Только создатель квиза может остановить
    if message.from_user.id != session.quiz.owner_id:
        await message.answer(t("quiz.only_creator_stop", lang))
        return

    cancel_timer(session.id)
    await finish_session(db, session.id)

    # Показываем статистику
    rows = await get_group_stats(db, session.id)
    await message.answer(
        t("quiz.stopped_by_creator", lang)
        + fmt_group_results(rows, lang)
    )


# ---------------------------------------------------------------------------
# Присоединиться
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("join:"))
async def cb_join(call: CallbackQuery, lang: str) -> None:
    session_id = int(call.data.split(":")[1])

    async with AsyncSessionFactory() as db:
        async with db.begin():
            added = await add_participant(
                db, session_id,
                call.from_user.id, call.from_user.username
            )
            participants = await get_participants(db, session_id)

    if not added:
        await call.answer(t("quiz.already_in_game", lang), show_alert=False)
        return

    names = [p.username or t("quiz.participant_n", lang, n=i + 1) for i, p in enumerate(participants)]
    await call.answer(t("quiz.joined", lang), show_alert=False)
    await call.message.edit_text(
        call.message.text + "\n\n" + t("quiz.participants", lang, count=len(participants), names=", ".join(names)),
        reply_markup=join_kb(session_id, lang),
    )


@router.callback_query(F.data.startswith("already_joined:"))
async def cb_already_joined(call: CallbackQuery, lang: str) -> None:
    await call.answer(t("quiz.already_in_game", lang), show_alert=False)


# ---------------------------------------------------------------------------
# Начать (только создатель квиза)
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("start_group:"))
async def cb_start_group(call: CallbackQuery, lang: str) -> None:
    session_id = int(call.data.split(":")[1])

    async with AsyncSessionFactory() as db:
        async with db.begin():
            session = await get_session(db, session_id)
            if session is None:
                await call.answer(t("common.session_not_found", lang), show_alert=True)
                return

            if call.from_user.id != session.quiz.owner_id:
                await call.answer(t("quiz.only_creator_start", lang), show_alert=True)
                return

            participants = await get_participants(db, session_id)
            if not participants:
                await call.answer(t("quiz.no_participants", lang), show_alert=True)
                return
            if len(participants) < 2:
                await call.answer(t("quiz.need_two", lang), show_alert=True)
                return

            await start_group_session(db, session_id)

            question_ids = build_question_order(session.quiz)
            await save_question_order(session_id, question_ids)

    await call.message.edit_text(t("quiz.group_starting", lang, count=len(participants)))

    await _send_question_group(session_id, 0, call.bot)


# ---------------------------------------------------------------------------
# Ответ в групповом режиме
# ---------------------------------------------------------------------------

@router.poll_answer()
async def on_poll_answer_group(poll_answer: PollAnswer, bot) -> None:
    poll_data = await get_poll_session(poll_answer.poll_id)
    if poll_data is None:
        return

    session_id, question_id, answer_ids = poll_data

    async with AsyncSessionFactory() as db:
        async with db.begin():
            session = await get_session(db, session_id)
            if session is None or session.status == SessionStatus.finished:
                return
            if session.mode != SessionMode.group:
                raise SkipHandler()

            user_id = poll_answer.user.id

            if await already_answered(db, session_id, question_id, user_id):
                return

            question = next((q for q in session.quiz.questions if q.id == question_id), None)
            if question is None:
                return

            chosen_idx = poll_answer.option_ids[0] if poll_answer.option_ids else None
            answer_id = None
            if chosen_idx is not None:
                if answer_ids is not None and chosen_idx < len(answer_ids):
                    answer_id = answer_ids[chosen_idx]
                else:
                    answers = get_ordered_answers(question, session.quiz.shuffle_a)
                    answer_id = answers[chosen_idx].id if chosen_idx < len(answers) else None

            await record_response(db, session_id, question_id, user_id, answer_id)

        answered_key = RedisKeys.question_answered(session_id, question_id)
        await sadd_member(answered_key, user_id, ex=3600)


# ---------------------------------------------------------------------------
# Отправка вопроса и колбэк таймера
# ---------------------------------------------------------------------------

async def _send_question_group(session_id: int, question_idx: int, bot) -> None:
    """Отправляет вопрос группе под замком сессии (защита от дублей)."""
    async with get_session_lock(session_id):
        await _send_question_group_locked(session_id, question_idx, bot)


async def _send_question_group_locked(session_id: int, question_idx: int, bot) -> None:
    """Отправляет вопрос группе и запускает таймер."""
    async with AsyncSessionFactory() as db:
        async with db.begin():
            session = await get_session(db, session_id)
            if session is None or session.status == SessionStatus.finished:
                return

            order = await get_question_order(session_id)
            if question_idx >= len(order):
                await _finish_group(session_id, bot)
                return

            # Защита от гонки/двойного срабатывания таймера: этот вопрос уже
            # отправлен (сессия уже на нём или дальше) — не отправляем повторно.
            if question_idx != 0 and session.current_question_idx >= question_idx:
                return

            question_id = order[question_idx]
            question = next((q for q in session.quiz.questions if q.id == question_id), None)
            if question is None:
                return

            await advance_question(db, session_id, question_idx)
            answers = get_ordered_answers(question, session.quiz.shuffle_a)
            correct_idx = next(i for i, a in enumerate(answers) if a.is_correct)
            timer_sec = session.quiz.timer_sec
            chat_id = session.chat_id
            lang = await get_lang(db, session.quiz.owner_id)

    question_text, options = build_poll_data(question, answers)

    # Пауза перед следующим вопросом (кроме первого)
    if question_idx > 0:
        await asyncio.sleep(2)

    await maybe_send_long_question(chat_id, question, answers, bot)

    # Счётчик прогресса
    await bot.send_message(
        chat_id,
        t("start.progress", lang, num=question_idx + 1, total=len(order))
    )

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
        question_id,
        answer_ids=[a.id for a in answers],
        ttl=timer_sec + 60,
    )

    await start_question_timer(
        session_id, question_id, timer_sec,
        lambda sid, b: _on_timer_group(sid, question_idx, b),
        bot,
    )


async def _on_timer_group(session_id: int, current_idx: int, bot) -> None:
    """Колбэк таймера — переходим к следующему вопросу."""
    async with AsyncSessionFactory() as db:
        async with db.begin():
            session = await get_session(db, session_id)
            if session is None or session.status == SessionStatus.finished:
                return

            order = await get_question_order(session_id)
            if current_idx < len(order):
                question_id = order[current_idx]
                answered_key = RedisKeys.question_answered(session_id, question_id)
                answered_user_ids = {int(user_id) for user_id in await smembers(answered_key)}
                all_user_ids = [p.user_id for p in session.participants]
                await record_skipped_responses(
                    db,
                    session_id,
                    question_id,
                    answered_user_ids,
                    all_user_ids,
                )

    await _send_question_group(session_id, current_idx + 1, bot)


async def _finish_group(session_id: int, bot) -> None:
    """Завершает групповую сессию и выводит статистику."""
    async with AsyncSessionFactory() as db:
        async with db.begin():
            session = await get_session(db, session_id)
            if session is None:
                return
            await finish_session(db, session_id)
            rows = await get_group_stats(db, session_id)
            q_stats = await get_group_question_stats(db, session_id)
            chat_id = session.chat_id
            lang = await get_lang(db, session.quiz.owner_id)

    await bot.send_message(chat_id, fmt_group_results_detailed(rows, q_stats, lang))
    await bot.send_message(
        chat_id,
        t("quiz.download_results_q", lang),
        reply_markup=export_group_kb(session_id, lang),
    )
