"""
services/session_service.py
Создание, управление и завершение сессий (solo / group).
"""
import random
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Session, SessionMode, SessionStatus, SessionUser, Quiz, Question


# Единый набор опций eager-load — используется везде где нужна сессия с quiz+questions+answers
_SESSION_OPTIONS = [
    selectinload(Session.quiz)
        .selectinload(Quiz.questions)
        .selectinload(Question.answers),
    selectinload(Session.participants),
]


async def _load_session(db: AsyncSession, session_id: int) -> Session | None:
    """Загружает сессию со всеми связями (quiz, questions, answers, participants)."""
    result = await db.execute(
        select(Session)
        .where(Session.id == session_id)
        .options(*_SESSION_OPTIONS)
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Создание сессии
# ---------------------------------------------------------------------------

async def create_solo_session(
    db: AsyncSession, quiz_id: int, chat_id: int, user_id: int, username: str | None,
    plan_item_id: int | None = None,
) -> Session:
    """Создаёт solo-сессию и сразу добавляет единственного участника.

    plan_item_id != None — сессия запущена «с регистрацией» из планера:
    её результат засчитается в план при полном прохождении.
    """
    session = Session(
        quiz_id=quiz_id,
        chat_id=chat_id,
        mode=SessionMode.solo,
        status=SessionStatus.active,
        current_question_idx=0,
        started_at=datetime.now(timezone.utc),
        plan_item_id=plan_item_id,
    )
    db.add(session)
    await db.flush()  # получаем session.id

    db.add(SessionUser(session_id=session.id, user_id=user_id, username=username))
    await db.flush()

    # Перезагружаем с eager-load чтобы не было lazy-load ошибок
    return await _load_session(db, session.id)


async def create_group_session(db: AsyncSession, quiz_id: int, chat_id: int) -> Session:
    """Создаёт групповую сессию в статусе waiting — ждём участников."""
    session = Session(
        quiz_id=quiz_id,
        chat_id=chat_id,
        mode=SessionMode.group,
        status=SessionStatus.waiting,
        current_question_idx=0,
    )
    db.add(session)
    await db.flush()

    return await _load_session(db, session.id)


# ---------------------------------------------------------------------------
# Участники (group)
# ---------------------------------------------------------------------------

async def add_participant(
    db: AsyncSession, session_id: int, user_id: int, username: str | None
) -> bool:
    """
    Добавляет участника в сессию.
    Возвращает False если уже присоединился.
    """
    existing = await db.execute(
        select(SessionUser)
        .where(SessionUser.session_id == session_id, SessionUser.user_id == user_id)
    )
    if existing.scalar_one_or_none():
        return False

    db.add(SessionUser(session_id=session_id, user_id=user_id, username=username))
    return True


async def get_participants(db: AsyncSession, session_id: int) -> list[SessionUser]:
    result = await db.execute(
        select(SessionUser).where(SessionUser.session_id == session_id)
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Получение сессии
# ---------------------------------------------------------------------------

async def get_session(db: AsyncSession, session_id: int) -> Session | None:
    return await _load_session(db, session_id)


async def get_active_session_by_chat(db: AsyncSession, chat_id: int) -> Session | None:
    """Находит активную (не завершённую) сессию в чате, с eager-load."""
    result = await db.execute(
        select(Session)
        .where(Session.chat_id == chat_id, Session.status != SessionStatus.finished)
        .order_by(Session.id.desc())
        .options(*_SESSION_OPTIONS)
    )
    return result.scalars().first()


# ---------------------------------------------------------------------------
# Управление ходом сессии
# ---------------------------------------------------------------------------

async def start_group_session(db: AsyncSession, session_id: int) -> None:
    """Переводит групповую сессию из waiting → active."""
    await db.execute(
        update(Session)
        .where(Session.id == session_id)
        .values(status=SessionStatus.active, started_at=datetime.now(timezone.utc))
    )


async def advance_question(db: AsyncSession, session_id: int, next_idx: int) -> None:
    """Переключает current_question_idx на следующий вопрос."""
    await db.execute(
        update(Session)
        .where(Session.id == session_id)
        .values(current_question_idx=next_idx)
    )


async def finish_session(db: AsyncSession, session_id: int) -> None:
    """Помечает сессию как завершённую."""
    await db.execute(
        update(Session)
        .where(Session.id == session_id)
        .values(status=SessionStatus.finished, finished_at=datetime.now(timezone.utc))
    )


# ---------------------------------------------------------------------------
# Порядок вопросов в сессии (хранится в Redis как список id)
# ---------------------------------------------------------------------------

def build_question_order(quiz: Quiz) -> list[int]:
    """
    Возвращает список question_id в нужном порядке (с учётом shuffle_q).
    """
    ids = [q.id for q in sorted(quiz.questions, key=lambda q: q.position)]
    if quiz.shuffle_q:
        random.shuffle(ids)
    return ids
