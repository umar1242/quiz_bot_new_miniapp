"""
services/admin_service.py
Агрегаты и выборки для глобальной админ-панели.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import (
    Answer, Card, Deck, Question, Quiz,
    Response, Session, SessionMode, SessionStatus, UserSettings,
)

RECENT_LIMIT = 10


@dataclass(slots=True)
class BotStats:
    users_total: int
    users_banned: int
    quizzes_total: int
    questions_total: int
    sessions_total: int
    sessions_finished: int
    answers_total: int
    sessions_active: int
    sessions_waiting: int
    sessions_solo: int
    sessions_group: int
    quizzes_24h: int
    sessions_24h: int
    answers_24h: int
    decks_total: int
    cards_total: int
    generated_at: datetime

    @property
    def avg_questions(self) -> float:
        return self.questions_total / self.quizzes_total if self.quizzes_total else 0.0


async def _count(db: AsyncSession, model, *where) -> int:
    stmt = select(func.count()).select_from(model)
    for cond in where:
        stmt = stmt.where(cond)
    return int((await db.execute(stmt)).scalar() or 0)


async def bot_stats(db: AsyncSession) -> BotStats:
    cutoff = datetime.utcnow() - timedelta(hours=24)
    return BotStats(
        users_total=await _count(db, UserSettings),
        users_banned=await _count(db, UserSettings, UserSettings.banned == True),   # noqa: E712
        quizzes_total=await _count(db, Quiz),
        questions_total=await _count(db, Question),
        sessions_total=await _count(db, Session),
        sessions_finished=await _count(db, Session, Session.status == SessionStatus.finished),
        answers_total=await _count(db, Response),
        sessions_active=await _count(db, Session, Session.status == SessionStatus.active),
        sessions_waiting=await _count(db, Session, Session.status == SessionStatus.waiting),
        sessions_solo=await _count(db, Session, Session.mode == SessionMode.solo),
        sessions_group=await _count(db, Session, Session.mode == SessionMode.group),
        quizzes_24h=await _count(db, Quiz, Quiz.created_at >= cutoff),
        sessions_24h=await _count(db, Session, Session.started_at >= cutoff),
        answers_24h=await _count(db, Response, Response.answered_at >= cutoff),
        decks_total=await _count(db, Deck),
        cards_total=await _count(db, Card),
        generated_at=datetime.now(),
    )


async def recent_quizzes(db: AsyncSession, limit: int = RECENT_LIMIT) -> list[Quiz]:
    result = await db.execute(
        select(Quiz)
        .order_by(Quiz.created_at.desc())
        .limit(limit)
        .options(selectinload(Quiz.questions))
    )
    return list(result.scalars().all())


async def search_quizzes(db: AsyncSession, query: str, limit: int = RECENT_LIMIT) -> list[Quiz]:
    query = query.strip()
    conditions = [Quiz.title.ilike(f"%{query}%")]
    if query.isdigit():
        conditions.append(Quiz.id == int(query))
    result = await db.execute(
        select(Quiz)
        .where(or_(*conditions))
        .order_by(Quiz.created_at.desc())
        .limit(limit)
        .options(selectinload(Quiz.questions))
    )
    return list(result.scalars().all())


async def delete_quiz(db: AsyncSession, quiz: Quiz) -> None:
    await db.delete(quiz)
    await db.flush()


async def recent_decks(db: AsyncSession, limit: int = RECENT_LIMIT) -> list[Deck]:
    result = await db.execute(
        select(Deck)
        .order_by(Deck.created_at.desc())
        .limit(limit)
        .options(selectinload(Deck.cards))
    )
    return list(result.scalars().all())


async def search_decks(db: AsyncSession, query: str, limit: int = RECENT_LIMIT) -> list[Deck]:
    query = query.strip()
    conditions = [Deck.title.ilike(f"%{query}%")]
    if query.isdigit():
        conditions.append(Deck.id == int(query))
    result = await db.execute(
        select(Deck)
        .where(or_(*conditions))
        .order_by(Deck.created_at.desc())
        .limit(limit)
        .options(selectinload(Deck.cards))
    )
    return list(result.scalars().all())


async def delete_deck_admin(db: AsyncSession, deck: Deck) -> None:
    await db.delete(deck)
    await db.flush()
