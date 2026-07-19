"""
services/quiz_service.py
CRUD операции над Quiz, Question, Answer.
Роутеры работают только через этот сервис — не трогают БД напрямую.
"""
import random
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Quiz, Question, Answer
from dto.quiz_dto import QuizCreateDTO, QuestionDTO


# ---------------------------------------------------------------------------
# Quiz
# ---------------------------------------------------------------------------

async def create_quiz(db: AsyncSession, dto: QuizCreateDTO) -> Quiz:
    """Создаёт квиз с вопросами и ответами из DTO. Возвращает сохранённый объект."""
    quiz = Quiz(
        owner_id=dto.owner_id,
        title=dto.title,
        timer_sec=dto.timer_sec,
        shuffle_q=dto.shuffle_q,
        shuffle_a=dto.shuffle_a,
    )
    db.add(quiz)
    await db.flush()  # получаем quiz.id до коммита

    for pos, q_dto in enumerate(dto.questions, start=1):
        question = Question(
            quiz_id=quiz.id,
            position=pos,
            text=q_dto.text,
            explanation=q_dto.explanation,
        )
        db.add(question)
        await db.flush()  # получаем question.id

        for a_pos, a_dto in enumerate(q_dto.answers, start=1):
            answer = Answer(
                question_id=question.id,
                position=a_pos,
                text=a_dto.text,
                is_correct=a_dto.is_correct,
            )
            db.add(answer)

    # Перезагружаем с вопросами и ответами (нужно для fmt_quiz_saved → len(quiz.questions))
    return await get_quiz(db, quiz.id)


async def get_quiz(db: AsyncSession, quiz_id: int) -> Quiz | None:
    """Загружает квиз со всеми вопросами и ответами (eager load)."""
    result = await db.execute(
        select(Quiz)
        .where(Quiz.id == quiz_id)
        .options(
            selectinload(Quiz.questions).selectinload(Question.answers)
        )
    )
    return result.scalar_one_or_none()


async def get_user_quizzes(db: AsyncSession, owner_id: int) -> list[Quiz]:
    """Список квизов пользователя (с количеством вопросов для отображения)."""
    result = await db.execute(
        select(Quiz)
        .where(Quiz.owner_id == owner_id)
        .order_by(Quiz.created_at.desc())
        .options(selectinload(Quiz.questions))
    )
    return list(result.scalars().all())


async def delete_quiz(db: AsyncSession, quiz_id: int, owner_id: int) -> bool:
    """Удаляет квиз. Возвращает True если удалён, False если не найден / не владелец."""
    result = await db.execute(
        delete(Quiz)
        .where(Quiz.id == quiz_id, Quiz.owner_id == owner_id)
        .returning(Quiz.id)
    )
    return result.scalar_one_or_none() is not None


async def update_quiz_settings(
    db: AsyncSession,
    quiz_id: int,
    owner_id: int,
    *,
    timer_sec: int | None = None,
    shuffle_q: bool | None = None,
    shuffle_a: bool | None = None,
    title: str | None = None,
) -> Quiz | None:
    """Обновляет настройки квиза. Возвращает обновлённый объект или None."""
    values: dict = {}
    if timer_sec  is not None: values["timer_sec"]  = timer_sec
    if shuffle_q  is not None: values["shuffle_q"]  = shuffle_q
    if shuffle_a  is not None: values["shuffle_a"]  = shuffle_a
    if title      is not None: values["title"]       = title

    if not values:
        return await get_quiz(db, quiz_id)

    await db.execute(
        update(Quiz)
        .where(Quiz.id == quiz_id, Quiz.owner_id == owner_id)
        .values(**values)
    )
    return await get_quiz(db, quiz_id)


# ---------------------------------------------------------------------------
# Question
# ---------------------------------------------------------------------------

async def get_question(db: AsyncSession, question_id: int) -> Question | None:
    result = await db.execute(
        select(Question)
        .where(Question.id == question_id)
        .options(selectinload(Question.answers))
    )
    return result.scalar_one_or_none()


async def delete_question(db: AsyncSession, question_id: int, owner_id: int) -> bool:
    """
    Удаляет вопрос и пересчитывает position оставшихся вопросов квиза.
    owner_id проверяется через JOIN с Quiz.
    """
    # Сначала убеждаемся что вопрос принадлежит квизу этого владельца
    result = await db.execute(
        select(Question.id, Question.quiz_id, Question.position)
        .join(Quiz, Quiz.id == Question.quiz_id)
        .where(Question.id == question_id, Quiz.owner_id == owner_id)
    )
    row = result.one_or_none()
    if row is None:
        return False

    _, quiz_id, deleted_pos = row

    await db.execute(delete(Question).where(Question.id == question_id))

    # Сдвигаем position у всех вопросов после удалённого
    remaining = await db.execute(
        select(Question)
        .where(Question.quiz_id == quiz_id, Question.position > deleted_pos)
        .order_by(Question.position)
    )
    for q in remaining.scalars().all():
        q.position -= 1

    return True


async def replace_question(
    db: AsyncSession,
    question_id: int,
    owner_id: int,
    new_dto: QuestionDTO,
) -> Question | None:
    """
    Заменяет текст и ответы вопроса на новые из DTO.
    Старые ответы удаляются, создаются новые.
    """
    result = await db.execute(
        select(Question)
        .join(Quiz, Quiz.id == Question.quiz_id)
        .where(Question.id == question_id, Quiz.owner_id == owner_id)
        .options(selectinload(Question.answers))
    )
    question = result.scalar_one_or_none()
    if question is None:
        return None

    question.text = new_dto.text
    question.explanation = new_dto.explanation

    # Удаляем старые ответы
    await db.execute(delete(Answer).where(Answer.question_id == question_id))

    # Создаём новые
    for pos, a_dto in enumerate(new_dto.answers, start=1):
        db.add(Answer(
            question_id=question_id,
            position=pos,
            text=a_dto.text,
            is_correct=a_dto.is_correct,
        ))

    return await get_question(db, question_id)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_ordered_questions(quiz: Quiz) -> list[Question]:
    """Возвращает вопросы с учётом shuffle_q настройки квиза."""
    questions = list(quiz.questions)
    if quiz.shuffle_q:
        random.shuffle(questions)
    return questions


def get_ordered_answers(question: Question, shuffle: bool) -> list[Answer]:
    """Возвращает ответы с учётом shuffle_a настройки."""
    answers = list(question.answers)
    if shuffle:
        random.shuffle(answers)
    return answers
