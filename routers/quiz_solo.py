"""
routers/quiz_solo.py
Обработка ответов и переключение вопросов в solo-режиме.
"""
import asyncio
import logging

from aiogram import Router, F
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.filters import Command
from aiogram.types import PollAnswer, Message

from db.base import AsyncSessionFactory
from db.models import SessionMode, SessionStatus
from services.response_service import record_response, already_answered
from services.session_service import get_session, advance_question, finish_session, get_active_session_by_chat
from services.stats_service import get_solo_stats, get_question_stats
from services.timer_service import (
    get_poll_session, get_question_order,
    save_poll_session, cancel_timer, start_question_timer,
    get_session_lock,
)
from services.quiz_service import get_ordered_answers
from services.user_service import get_lang
from utils.formatters import fmt_solo_result, fmt_solo_result_detailed
from utils.i18n import t
from keyboards.edit_kb import replay_kb, export_solo_kb
from utils.poll_utils import build_poll_data, maybe_send_long_question

logger = logging.getLogger(__name__)
router = Router()

# ---------------------------------------------------------------------------
# Остановка квиза — /stop
# ---------------------------------------------------------------------------

@router.message(Command("stop", ignore_mention=True), F.chat.type == "private")
async def cmd_stop_solo(message: Message, db, lang: str) -> None:
    """Останавливает текущий квиз в личном чате."""
    # Ищем активную сессию этого чата
    session = await get_active_session_by_chat(db, message.chat.id)

    if session is None:
        await message.answer(t("quiz.no_active", lang))
        return

    # В личном чате — только solo
    if session.mode != SessionMode.solo:
        return

    # Проверяем что это участник сессии
    is_participant = any(p.user_id == message.from_user.id for p in session.participants)
    if not is_participant:
        await message.answer(t("quiz.not_participant", lang))
        return

    cancel_timer(session.id)
    await finish_session(db, session.id)

    # Показываем частичную статистику
    stats = await get_solo_stats(db, session.id, message.from_user.id)
    await message.answer(
        t("quiz.stopped", lang)
        + fmt_solo_result(stats["correct"], stats["wrong"], stats["skipped"], stats["total_sec"], lang)
    )


# ---------------------------------------------------------------------------
# Ответ пользователя на poll
# ---------------------------------------------------------------------------

@router.poll_answer()
async def on_poll_answer(poll_answer: PollAnswer, bot) -> None:
    """Принимает ответ пользователя на Quiz Poll."""
    poll_data = await get_poll_session(poll_answer.poll_id)
    if poll_data is None:
        return

    session_id, question_id, answer_ids = poll_data

    async with AsyncSessionFactory() as db:
        async with db.begin():
            session = await get_session(db, session_id)
            if session is None or session.status == SessionStatus.finished:
                return
            if session.mode != SessionMode.solo:
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

    cancel_timer(session_id)
    await _next_question(session_id, bot, from_question_id=question_id)


async def _next_question(session_id: int, bot, from_question_id: int | None = None) -> None:
    """Переход к следующему вопросу под замком сессии (защита от гонки таймер+ответ)."""
    async with get_session_lock(session_id):
        await _next_question_locked(session_id, bot, from_question_id)


async def _next_question_locked(session_id: int, bot, from_question_id: int | None = None) -> None:
    """Отправляет следующий вопрос или завершает сессию."""
    async with AsyncSessionFactory() as db:
        async with db.begin():
            session = await get_session(db, session_id)
            if session is None or session.status == SessionStatus.finished:
                return

            order = await get_question_order(session_id)

            # Защита от гонки: если сессия уже ушла с этого вопроса, значит
            # следующий вопрос уже отправил другой обработчик — выходим, чтобы
            # не отправить второй вопрос за один шаг.
            if (
                from_question_id is not None
                and session.current_question_idx < len(order)
                and order[session.current_question_idx] != from_question_id
            ):
                return
            user_id = session.participants[0].user_id if session.participants else None
            lang = await get_lang(db, user_id) if user_id is not None else "ru"
            if user_id is not None and session.current_question_idx < len(order):
                current_question_id = order[session.current_question_idx]
                if not await already_answered(db, session_id, current_question_id, user_id):
                    await record_response(db, session_id, current_question_id, user_id, None)

            next_idx = session.current_question_idx + 1

            if next_idx >= len(order):
                await finish_session(db, session_id)
                if user_id is None:
                    return
                stats = await get_solo_stats(db, session_id, user_id)
                q_stats = await get_question_stats(db, session_id, user_id)
                quiz_id = session.quiz_id
                # Планер: засчитываем прохождение ТОЛЬКО если квиз запущен
                # «с регистрацией» из планера И доведён до конца (мы здесь).
                if session.plan_item_id:
                    from services.planner_service import log_registered_event
                    from db.models import StudyKind
                    await log_registered_event(
                        db, user_id, session.plan_item_id, StudyKind.quiz, quiz_id,
                        correct=stats["correct"],
                        total=stats["correct"] + stats["wrong"] + stats["skipped"],
                    )
                await bot.send_message(
                    session.chat_id,
                    fmt_solo_result_detailed(
                        stats["correct"], stats["wrong"],
                        stats["skipped"], stats["total_sec"],
                        question_stats=q_stats, lang=lang,
                    ),
                    reply_markup=replay_kb(quiz_id, lang),
                )
                # Отдельное сообщение с кнопкой экспорта
                await bot.send_message(
                    session.chat_id,
                    t("quiz.save_results_q", lang),
                    reply_markup=export_solo_kb(session_id, lang),
                )
                return

            next_question_id = order[next_idx]
            question = next((q for q in session.quiz.questions if q.id == next_question_id), None)
            if question is None:
                return

            await advance_question(db, session_id, next_idx)
            answers = get_ordered_answers(question, session.quiz.shuffle_a)
            correct_idx = next(i for i, a in enumerate(answers) if a.is_correct)
            total_questions = len(order)
            chat_id = session.chat_id
            timer_sec = session.quiz.timer_sec

            question_text, options = build_poll_data(question, answers)

        # Пауза перед следующим вопросом — даём пользователю увидеть правильный ответ
        await asyncio.sleep(2)

        await maybe_send_long_question(chat_id, question, answers, bot)

        # Счётчик прогресса перед поллом
        await bot.send_message(
            chat_id,
            t("start.progress", lang, num=next_idx + 1, total=total_questions)
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
            poll_msg.poll.id, session_id, question.id,
            answer_ids=[a.id for a in answers],
            ttl=timer_sec + 60
        )

        await start_question_timer(
            session_id, question.id,
            timer_sec,
            lambda sid, b, qid=question.id: _next_question(sid, b, from_question_id=qid),
            bot,
        )
