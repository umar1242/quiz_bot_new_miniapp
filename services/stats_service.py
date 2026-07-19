"""
services/stats_service.py
Агрегация статистики из таблицы responses.
"""
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Response, SessionUser


async def get_solo_stats(db: AsyncSession, session_id: int, user_id: int) -> dict:
    """
    Возвращает dict:
      correct, wrong, skipped, total_sec
    """
    result = await db.execute(
        select(
            func.count().filter(Response.is_correct == True).label("correct"),   # noqa: E712
            func.count().filter(
                Response.is_correct == False, Response.answer_id != None         # noqa: E712, E711
            ).label("wrong"),
            func.count().filter(Response.answer_id == None).label("skipped"),    # noqa: E711
            func.extract(
                "epoch",
                func.max(Response.answered_at) - func.min(Response.answered_at)
            ).label("total_sec"),
        )
        .where(Response.session_id == session_id, Response.user_id == user_id)
    )
    row = result.one()
    return {
        "correct":   int(row.correct or 0),
        "wrong":     int(row.wrong or 0),
        "skipped":   int(row.skipped or 0),
        "total_sec": int(row.total_sec or 0),
    }


async def get_quiz_respondents_count(db: AsyncSession, quiz_id: int) -> int:
    """
    Возвращает количество уникальных пользователей,
    которые прошли хотя бы одну сессию этого квиза.
    """
    from db.models import Session
    result = await db.execute(
        select(func.count(func.distinct(Response.user_id)))
        .join(Session, Session.id == Response.session_id)
        .where(Session.quiz_id == quiz_id)
    )
    return int(result.scalar() or 0)


async def get_group_stats(db: AsyncSession, session_id: int) -> list[dict]:
    """
    Возвращает список dict (отсортировано по убыванию correct):
      username, correct, total
    Включает только тех кто ответил хотя бы на 1 вопрос.
    """
    result = await db.execute(
        select(
            SessionUser.username,
            SessionUser.user_id,
            func.count().filter(Response.is_correct == True).label("correct"),  # noqa: E712
            func.count().label("total"),
        )
        .join(Response, Response.user_id == SessionUser.user_id)
        .where(Response.session_id == session_id, SessionUser.session_id == session_id)
        .group_by(SessionUser.user_id, SessionUser.username)
        .order_by(func.count().filter(Response.is_correct == True).desc())       # noqa: E712
    )
    rows = result.all()
    return [
        {"username": r.username, "user_id": r.user_id, "correct": int(r.correct), "total": int(r.total)}
        for r in rows
    ]

async def get_respondents_batch(db: AsyncSession, quiz_ids: list[int]) -> dict[int, int]:
    """
    Одним запросом возвращает dict {quiz_id: unique_respondents}
    для списка квизов. Заменяет N отдельных get_quiz_respondents_count.
    """
    if not quiz_ids:
        return {}
    from db.models import Session
    result = await db.execute(
        select(
            Session.quiz_id,
            func.count(func.distinct(Response.user_id)).label("cnt"),
        )
        .join(Session, Session.id == Response.session_id)
        .where(Session.quiz_id.in_(quiz_ids))
        .group_by(Session.quiz_id)
    )
    return {row.quiz_id: int(row.cnt) for row in result.all()}


async def get_question_stats(db: AsyncSession, session_id: int, user_id: int) -> list[dict]:
    """
    Для соло-режима: детальная статистика по каждому вопросу.
    Возвращает список dict: {question_text, is_correct, answer_text, time_sec}
    """
    from db.models import Question, Answer
    result = await db.execute(
        select(
            Question.text.label("question_text"),
            Response.is_correct,
            Answer.text.label("answer_text"),
            Response.answered_at,
        )
        .join(Question, Question.id == Response.question_id)
        .outerjoin(Answer, Answer.id == Response.answer_id)
        .where(Response.session_id == session_id, Response.user_id == user_id)
        .order_by(Response.answered_at)
    )
    rows = result.all()
    items = []
    for i, r in enumerate(rows):
        items.append({
            "num": i + 1,
            "question_text": r.question_text,
            "is_correct": r.is_correct,
            "answer_text": r.answer_text,
        })
    return items


async def get_group_question_stats(db: AsyncSession, session_id: int) -> list[dict]:
    """
    Для группового режима: по каждому вопросу — сколько % ответили правильно.
    Возвращает список dict: {num, question_text, correct_count, total_count, pct}
    """
    from db.models import Question
    result = await db.execute(
        select(
            Question.position.label("num"),
            Question.text.label("question_text"),
            func.count().filter(Response.is_correct == True).label("correct_count"),  # noqa: E712
            func.count().label("total_count"),
        )
        .join(Question, Question.id == Response.question_id)
        .where(Response.session_id == session_id)
        .group_by(Question.id, Question.position, Question.text)
        .order_by(Question.position)
    )
    rows = result.all()
    return [
        {
            "num": r.num,
            "question_text": r.question_text,
            "correct_count": int(r.correct_count),
            "total_count": int(r.total_count),
            "pct": round(r.correct_count / r.total_count * 100) if r.total_count else 0,
        }
        for r in rows
    ]
