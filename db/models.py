from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class UserSettings(Base):
    """Настройки пользователя."""
    __tablename__ = "user_settings"

    user_id: Mapped[int]  = mapped_column(BigInteger, primary_key=True)
    lang: Mapped[str]     = mapped_column(String(2), nullable=False, default="ru")
    banned: Mapped[bool]  = mapped_column(Boolean, nullable=False, default=False)


class SessionMode(PyEnum):
    solo  = "solo"
    group = "group"


class SessionStatus(PyEnum):
    waiting  = "waiting"   # ждём участников (только group)
    active   = "active"    # идёт квиз
    finished = "finished"  # завершён


# ---------------------------------------------------------------------------
# Quiz & questions
# ---------------------------------------------------------------------------

class Quiz(Base):
    __tablename__ = "quizzes"

    id: Mapped[int]         = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int]   = mapped_column(BigInteger, nullable=False, index=True)
    title: Mapped[str]      = mapped_column(String(255), nullable=False, default="Без названия")
    timer_sec: Mapped[int]  = mapped_column(Integer, nullable=False, default=30)
    shuffle_q: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    shuffle_a: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # relations
    questions: Mapped[list["Question"]] = relationship(
        "Question", back_populates="quiz", cascade="all, delete-orphan",
        order_by="Question.position",
    )
    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="quiz", cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int]       = mapped_column(Integer, primary_key=True)
    quiz_id: Mapped[int]  = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)   # порядок в квизе
    text: Mapped[str]     = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)  # объяснение после ответа

    quiz: Mapped["Quiz"]                = relationship("Quiz", back_populates="questions")
    answers: Mapped[list["Answer"]]     = relationship(
        "Answer", back_populates="question", cascade="all, delete-orphan",
        order_by="Answer.position",
    )
    responses: Mapped[list["Response"]] = relationship(
        "Response", back_populates="question", cascade="all, delete-orphan"
    )


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[int]          = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
    position: Mapped[int]    = mapped_column(Integer, nullable=False)
    text: Mapped[str]        = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    question: Mapped["Question"] = relationship("Question", back_populates="answers")


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int]      = mapped_column(Integer, primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"), index=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)

    mode: Mapped[SessionMode]     = mapped_column(Enum(SessionMode), nullable=False)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus), nullable=False, default=SessionStatus.waiting
    )

    current_question_idx: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None]  = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Если сессия запущена «с регистрацией» из планера — id пункта плана (иначе NULL).
    # Прохождение засчитывается в план ТОЛЬКО при полном завершении такой сессии.
    plan_item_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    quiz: Mapped["Quiz"]                    = relationship("Quiz", back_populates="sessions")
    participants: Mapped[list["SessionUser"]] = relationship(
        "SessionUser", back_populates="session", cascade="all, delete-orphan"
    )
    responses: Mapped[list["Response"]]     = relationship(
        "Response", back_populates="session", cascade="all, delete-orphan"
    )


class SessionUser(Base):
    """Участники сессии (важно для группового режима)."""
    __tablename__ = "session_users"

    id: Mapped[int]          = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int]  = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int]     = mapped_column(BigInteger, nullable=False)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session: Mapped["Session"] = relationship("Session", back_populates="participants")


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class Response(Base):
    """Ответ конкретного пользователя на конкретный вопрос в сессии."""
    __tablename__ = "responses"

    id: Mapped[int]          = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int]  = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int]     = mapped_column(BigInteger, nullable=False, index=True)

    # answer_id = NULL если пользователь не успел ответить (таймер истёк)
    answer_id: Mapped[int | None]  = mapped_column(ForeignKey("answers.id"), nullable=True)
    is_correct: Mapped[bool]       = mapped_column(Boolean, nullable=False, default=False)
    answered_at: Mapped[datetime]  = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session:  Mapped["Session"]       = relationship("Session",  back_populates="responses")
    question: Mapped["Question"]      = relationship("Question", back_populates="responses")
    answer:   Mapped["Answer | None"] = relationship("Answer")


# ---------------------------------------------------------------------------
# Flashcards (флешкарты) — отдельная сущность, не связана с квизами
# ---------------------------------------------------------------------------

class Deck(Base):
    """Колода флешкарт пользователя."""
    __tablename__ = "decks"

    id: Mapped[int]       = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    title: Mapped[str]    = mapped_column(String(255), nullable=False, default="Без названия")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    cards: Mapped[list["Card"]] = relationship(
        "Card", back_populates="deck", cascade="all, delete-orphan",
        order_by="Card.position",
    )


class Card(Base):
    """Одна флешкарта: лицо (front) и оборот (back)."""
    __tablename__ = "cards"

    id: Mapped[int]       = mapped_column(Integer, primary_key=True)
    deck_id: Mapped[int]  = mapped_column(ForeignKey("decks.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)   # порядок в колоде
    front: Mapped[str]    = mapped_column(Text, nullable=False)      # лицевая сторона
    back: Mapped[str]     = mapped_column(Text, nullable=False)      # правильный оборот (true)
    back_false: Mapped[str | None] = mapped_column(Text, nullable=True)  # ложный оборот для теста «Верно/Неверно»

    deck: Mapped["Deck"] = relationship("Deck", back_populates="cards")


# ---------------------------------------------------------------------------
# Planner / трекер учёбы (Mini App) — лог активности, цели дня, отметки
# ---------------------------------------------------------------------------

class StudyKind(PyEnum):
    """Тип учебной активности, который логируется в StudyEvent."""
    quiz = "quiz"   # прохождение квиза (соло)
    anki = "anki"   # изучение колоды в Anki-режиме
    tf   = "tf"     # тест «Верно/Неверно» по колоде


class GoalKind(PyEnum):
    """К чему привязана цель дня."""
    deck   = "deck"    # цель по конкретной колоде (авто-отметка по активности)
    quiz   = "quiz"    # цель по конкретному квизу (авто-отметка)
    custom = "custom"  # своя цель без привязки (только ручная отметка)


class StudyEvent(Base):
    """
    Единый лог учебной активности — источник статистики для дашборда.
    Пишется при завершении квиза, изучения колоды и теста «Верно/Неверно».
    """
    __tablename__ = "study_events"

    id: Mapped[int]      = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    kind: Mapped[StudyKind] = mapped_column(Enum(StudyKind), nullable=False)
    ref_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # quiz_id / deck_id
    # Пункт плана, за который засчитано прохождение (регистрация из планера).
    plan_item_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    correct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total: Mapped[int]   = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class PlanGoal(Base):
    """Учебная цель («привычка») пользователя — аналог строки в трекере привычек."""
    __tablename__ = "plan_goals"

    id: Mapped[int]      = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    title: Mapped[str]   = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    goal_kind: Mapped[GoalKind]  = mapped_column(Enum(GoalKind), nullable=False, default=GoalKind.custom)
    ref_id: Mapped[int | None]   = mapped_column(BigInteger, nullable=True)  # deck_id / quiz_id
    target_per_day: Mapped[int]  = mapped_column(Integer, nullable=False, default=1)  # сколько раз за день
    weight: Mapped[int]  = mapped_column(Integer, nullable=False, default=1)          # вес во взвешенном балле
    color: Mapped[str]   = mapped_column(String(6), nullable=False, default="2E7D32")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class PlanCheck(Base):
    """Ручная отметка выполнения цели за конкретный день (YYYY-MM-DD, локальная дата)."""
    __tablename__ = "plan_checks"

    id: Mapped[int]      = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("plan_goals.id", ondelete="CASCADE"), index=True)
    day: Mapped[str]     = mapped_column(String(10), nullable=False)   # 'YYYY-MM-DD'
    done: Mapped[bool]   = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("goal_id", "day", name="uq_plancheck_goal_day"),
    )


# ---------------------------------------------------------------------------
# Учебный план (Mini App, новая модель): период + задания с целью «интервал»
# ---------------------------------------------------------------------------

class Plan(Base):
    """
    План на период: пользователь выбирает даты и набор заданий (квизы/колоды),
    для каждого — целевое число прохождений за период («интервал»).
    Активным считается ровно один план (последний созданный, active=True).
    """
    __tablename__ = "plans"

    id: Mapped[int]      = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_day: Mapped[str] = mapped_column(String(10), nullable=False)  # 'YYYY-MM-DD'
    end_day: Mapped[str]   = mapped_column(String(10), nullable=False)  # 'YYYY-MM-DD'
    active: Mapped[bool]   = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    items: Mapped[list["PlanItem"]] = relationship(
        "PlanItem", back_populates="plan", cascade="all, delete-orphan"
    )


class PlanItem(Base):
    """
    Задание плана: конкретный квиз или колода + целевое число прохождений.
    kind: 'quiz' — прохождение квиза; 'tf' — колода через тест «Верно/Неверно».
    Выполненные прохождения считаются по StudyEvent.plan_item_id.
    """
    __tablename__ = "plan_items"

    id: Mapped[int]      = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    kind: Mapped[str]    = mapped_column(String(8), nullable=False)   # 'quiz' | 'tf'
    ref_id: Mapped[int]  = mapped_column(BigInteger, nullable=False)  # quiz_id | deck_id
    title: Mapped[str]   = mapped_column(String(255), nullable=False, default="Задание")
    target: Mapped[int]  = mapped_column(Integer, nullable=False, default=1)  # «интервал» за период
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    plan: Mapped["Plan"] = relationship("Plan", back_populates="items")
