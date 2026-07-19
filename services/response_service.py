"""
services/response_service.py
Запись ответов пользователей и вспомогательные проверки.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Answer, Question, Response


async def record_response(
    db: AsyncSession,
    session_id: int,
    question_id: int,
    user_id: int,
    answer_id: int | None,
) -> Response:
    """
    Сохраняет ответ пользователя на вопрос.
    answer_id=None означает что пользователь не успел ответить (таймер истёк).
    is_correct вычисляется автоматически.
    """
    is_correct = False
    if answer_id is not None:
        result = await db.execute(
            select(Answer.is_correct).where(Answer.id == answer_id)
        )
        row = result.scalar_one_or_none()
        is_correct = bool(row)

    response = Response(
        session_id=session_id,
        question_id=question_id,
        user_id=user_id,
        answer_id=answer_id,
        is_correct=is_correct,
    )
    db.add(response)
    await db.flush()
    return response


async def already_answered(
    db: AsyncSession,
    session_id: int,
    question_id: int,
    user_id: int,
) -> bool:
    """Проверяет, отвечал ли уже этот пользователь на данный вопрос в сессии."""
    result = await db.execute(
        select(Response.id).where(
            Response.session_id == session_id,
            Response.question_id == question_id,
            Response.user_id == user_id,
        )
    )
    return result.scalar_one_or_none() is not None


async def get_correct_answer_id(db: AsyncSession, question_id: int) -> int | None:
    """Возвращает id правильного ответа для вопроса."""
    result = await db.execute(
        select(Answer.id).where(
            Answer.question_id == question_id,
            Answer.is_correct == True,  # noqa: E712
        )
    )
    return result.scalar_one_or_none()


async def record_skipped_responses(
    db: AsyncSession,
    session_id: int,
    question_id: int,
    answered_user_ids: set[int],
    all_user_ids: list[int],
) -> None:
    """
    Групповой режим: после истечения таймера записывает пропуск (answer_id=None)
    для участников которые не успели ответить.
    """
    for user_id in all_user_ids:
        if user_id in answered_user_ids:
            continue
        already = await already_answered(db, session_id, question_id, user_id)
        if not already:
            db.add(Response(
                session_id=session_id,
                question_id=question_id,
                user_id=user_id,
                answer_id=None,
                is_correct=False,
            ))
    await db.flush()
