"""
services/startup_service.py
Восстановление состояния после перезапуска бота.

При рестарте все asyncio-таймеры теряются. Этот модуль при старте:
  1. Находит все активные (active) сессии в БД
  2. Для solo-сессий — завершает их с сообщением пользователю
  3. Для group-сессий (active) — завершает аналогично
  4. Для group-сессий (waiting) — оставляет как есть,
     участники могут продолжить нажав "Начать"
"""
import logging

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from db.base import AsyncSessionFactory
from db.models import Session, SessionStatus, SessionMode, Quiz, Question
from services.session_service import finish_session
from services.stats_service import get_solo_stats, get_group_stats
from utils.formatters import fmt_solo_result, fmt_group_results

logger = logging.getLogger(__name__)


async def recover_on_startup(bot) -> None:
    """
    Вызывается один раз при старте бота.
    Завершает все зависшие active-сессии и уведомляет участников.
    """
    async with AsyncSessionFactory() as db:
        async with db.begin():
            result = await db.execute(
                select(Session)
                .where(Session.status == SessionStatus.active)
                .options(
                    selectinload(Session.quiz)
                        .selectinload(Quiz.questions)
                        .selectinload(Question.answers),
                    selectinload(Session.participants),
                )
            )
            active_sessions = list(result.scalars().all())

    if not active_sessions:
        logger.info("Startup recovery: активных сессий не найдено.")
        return

    logger.warning(
        "Startup recovery: найдено %d активных сессий — завершаем.",
        len(active_sessions)
    )

    for session in active_sessions:
        try:
            await _close_session(session, bot)
        except Exception as e:
            logger.exception("Ошибка при завершении сессии %s: %s", session.id, e)


async def _close_session(session: Session, bot) -> None:
    """Завершает одну зависшую сессию и отправляет уведомление."""
    async with AsyncSessionFactory() as db:
        async with db.begin():
            await finish_session(db, session.id)

            notice = "⚠️ <b>Бот был перезапущен — квиз прерван.</b>\n\n"

            if session.mode == SessionMode.solo and session.participants:
                user_id = session.participants[0].user_id
                stats = await get_solo_stats(db, session.id, user_id)
                text = notice + fmt_solo_result(
                    stats["correct"], stats["wrong"],
                    stats["skipped"], stats["total_sec"]
                )
            else:
                rows = await get_group_stats(db, session.id)
                text = notice + (fmt_group_results(rows) if rows else "Статистика недоступна.")

    try:
        await bot.send_message(session.chat_id, text)
    except Exception as e:
        logger.warning(
            "Не удалось отправить уведомление в chat_id=%s: %s",
            session.chat_id, e
        )

    logger.info(
        "Startup recovery: сессия %s (%s) завершена, chat_id=%s",
        session.id, session.mode.value, session.chat_id
    )
