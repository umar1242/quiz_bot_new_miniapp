from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
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


class SavedCross(Base):
    """Сохраненные скрещивания генетического калькулятора."""
    __tablename__ = "saved_crosses"

    id: Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parent1: Mapped[str] = mapped_column(String(255), nullable=False)
    parent2: Mapped[str] = mapped_column(String(255), nullable=False)
    phenotypes_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )



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
    cert = "cert"   # прохождение сертификационного теста


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


# ---------------------------------------------------------------------------
# Сертификационные тесты (Mini App): варианты в формате нацсертификата
# Y1 — один правильный ответ, Y2 — сопоставление, O1 — краткий открытый
# ответ, O2 — развёрнутая письменная работа с баллами по пунктам (M/A).
# ---------------------------------------------------------------------------

class CertQType(PyEnum):
    Y1 = "Y1"
    Y2 = "Y2"
    O1 = "O1"
    O2 = "O2"


class CertVariantStatus(PyEnum):
    draft = "draft"
    ready = "ready"


class CertVariant(Base):
    """Один вариант сертификационного теста (43 задания, 2 части)."""
    __tablename__ = "cert_variants"

    id: Mapped[int]       = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    title: Mapped[str]    = mapped_column(String(255), nullable=False, default="Вариант")
    status: Mapped[CertVariantStatus] = mapped_column(
        Enum(CertVariantStatus), nullable=False, default=CertVariantStatus.draft
    )
    # Тайминги двух частей теста (в секундах). По умолчанию — 100 и 80 минут.
    part1_timer_sec: Mapped[int] = mapped_column(Integer, nullable=False, default=100 * 60)
    part2_timer_sec: Mapped[int] = mapped_column(Integer, nullable=False, default=80 * 60)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    questions: Mapped[list["CertQuestion"]] = relationship(
        "CertQuestion", back_populates="variant", cascade="all, delete-orphan",
        order_by="CertQuestion.number",
    )


class CertQuestion(Base):
    """Одно задание варианта. Часть 1 (Y1/Y2/O1, №1-40) или часть 2 (O2, №41-43)."""
    __tablename__ = "cert_questions"

    id: Mapped[int]         = mapped_column(Integer, primary_key=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("cert_variants.id", ondelete="CASCADE"), index=True)
    number: Mapped[int]     = mapped_column(Integer, nullable=False)   # порядковый номер 1..43
    part: Mapped[int]       = mapped_column(Integer, nullable=False, default=1)  # 1 или 2
    qtype: Mapped[CertQType] = mapped_column(Enum(CertQType), nullable=False)
    text: Mapped[str]       = mapped_column(Text, nullable=False, default="")
    points: Mapped[int]     = mapped_column(Integer, nullable=False, default=1)
    # Выставляется парсером, если в тексте задания найден маркер рисунка —
    # такое задание нужно доредактировать в интерфейсе mini app (загрузить рисунок).
    needs_image: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    variant: Mapped["CertVariant"] = relationship("CertVariant", back_populates="questions")
    options: Mapped[list["CertOption"]] = relationship(
        "CertOption", back_populates="question", cascade="all, delete-orphan",
        order_by="CertOption.position",
    )
    match_pairs: Mapped[list["CertMatchPair"]] = relationship(
        "CertMatchPair", back_populates="question", cascade="all, delete-orphan",
        order_by="CertMatchPair.position",
    )
    open_answers: Mapped[list["CertOpenAnswer"]] = relationship(
        "CertOpenAnswer", back_populates="question", cascade="all, delete-orphan",
        order_by="CertOpenAnswer.id",
    )
    bands: Mapped[list["CertBand"]] = relationship(
        "CertBand", back_populates="question", cascade="all, delete-orphan",
        order_by="CertBand.band_no",
    )
    images: Mapped[list["CertQuestionImage"]] = relationship(
        "CertQuestionImage", back_populates="question", cascade="all, delete-orphan",
        order_by="CertQuestionImage.position",
    )


class CertOption(Base):
    """Вариант ответа Y1 (одна правильная альтернатива из 4)."""
    __tablename__ = "cert_options"

    id: Mapped[int]          = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("cert_questions.id", ondelete="CASCADE"), index=True)
    position: Mapped[int]    = mapped_column(Integer, nullable=False)
    text: Mapped[str]        = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    question: Mapped["CertQuestion"] = relationship("CertQuestion", back_populates="options")


class CertMatchPair(Base):
    """Пара для сопоставления Y2 (левый элемент ↔ правый элемент)."""
    __tablename__ = "cert_match_pairs"

    id: Mapped[int]          = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("cert_questions.id", ondelete="CASCADE"), index=True)
    position: Mapped[int]    = mapped_column(Integer, nullable=False)
    left_text: Mapped[str]   = mapped_column(Text, nullable=False)
    right_text: Mapped[str]  = mapped_column(Text, nullable=False)

    question: Mapped["CertQuestion"] = relationship("CertQuestion", back_populates="match_pairs")


class CertOpenAnswer(Base):
    """Эталонный(е) ответ(ы) для O1 — краткий открытый ответ, автопроверка."""
    __tablename__ = "cert_open_answers"

    id: Mapped[int]          = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("cert_questions.id", ondelete="CASCADE"), index=True)
    text: Mapped[str]        = mapped_column(Text, nullable=False)
    # 'exact' — точное совпадение (без учёта регистра/пробелов),
    # 'numeric' — сравнение чисел с допуском tolerance.
    match_mode: Mapped[str]  = mapped_column(String(16), nullable=False, default="exact")
    tolerance: Mapped[float | None] = mapped_column(nullable=True)

    question: Mapped["CertQuestion"] = relationship("CertQuestion", back_populates="open_answers")


class CertBand(Base):
    """Пункт (band) письменной работы O2 — эталонный ответ + макс. балл."""
    __tablename__ = "cert_bands"

    id: Mapped[int]          = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("cert_questions.id", ondelete="CASCADE"), index=True)
    band_no: Mapped[int]     = mapped_column(Integer, nullable=False)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_answer: Mapped[str] = mapped_column(Text, nullable=False, default="")
    match_mode: Mapped[str]  = mapped_column(String(16), nullable=False, default="numeric")
    tolerance: Mapped[float | None] = mapped_column(nullable=True)
    max_points: Mapped[int]  = mapped_column(Integer, nullable=False, default=1)

    question: Mapped["CertQuestion"] = relationship("CertQuestion", back_populates="bands")


class CertQuestionImage(Base):
    """Рисунок, прикреплённый к заданию через интерфейс mini app."""
    __tablename__ = "cert_question_images"

    id: Mapped[int]          = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("cert_questions.id", ondelete="CASCADE"), index=True)
    position: Mapped[int]    = mapped_column(Integer, nullable=False, default=0)
    file_path: Mapped[str]   = mapped_column(String(512), nullable=False)  # относительный путь в static/uploads
    caption: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    question: Mapped["CertQuestion"] = relationship("CertQuestion", back_populates="images")


class CertAttemptStatus(PyEnum):
    part1 = "part1"        # идёт тестовая часть (Y1/Y2/O1), общий таймер
    part2 = "part2"        # идёт письменная часть (O2), отдельный таймер
    finished = "finished"


class CertAttempt(Base):
    """Попытка прохождения варианта учеником (bot user)."""
    __tablename__ = "cert_attempts"

    id: Mapped[int]         = mapped_column(Integer, primary_key=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("cert_variants.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int]    = mapped_column(BigInteger, nullable=False, index=True)
    status: Mapped[CertAttemptStatus] = mapped_column(Enum(CertAttemptStatus), nullable=False, default=CertAttemptStatus.part1)

    part1_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    part1_deadline: Mapped[datetime]   = mapped_column(DateTime(timezone=True), nullable=False)
    part2_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    part2_deadline: Mapped[datetime | None]   = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None]      = mapped_column(DateTime(timezone=True), nullable=True)

    # Баллы считаются по мере ответа и на финализации попытки.
    points_part1: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    points_part2: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_part1: Mapped[int]    = mapped_column(Integer, nullable=False, default=0)
    max_part2: Mapped[int]    = mapped_column(Integer, nullable=False, default=0)

    variant: Mapped["CertVariant"] = relationship("CertVariant")
    responses: Mapped[list["CertResponse"]] = relationship(
        "CertResponse", back_populates="attempt", cascade="all, delete-orphan",
    )


class CertResponse(Base):
    """Ответ ученика на одно задание в рамках попытки."""
    __tablename__ = "cert_responses"
    __table_args__ = (UniqueConstraint("attempt_id", "question_id", name="uq_cert_response_attempt_question"),)

    id: Mapped[int]          = mapped_column(Integer, primary_key=True)
    attempt_id: Mapped[int]  = mapped_column(ForeignKey("cert_attempts.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("cert_questions.id", ondelete="CASCADE"), index=True)

    # Универсальное хранилище ответа: для Y1 — {"option_id": int},
    # для Y2 — {"pairs": {left_id: right_id, ...}}, для O1 — {"text": str},
    # для O2 — {"bands": {band_id: value, ...}, "image_url": str | None}.
    answer: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)  # None для O2 (не авто)
    points_earned: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    points_max: Mapped[float]    = mapped_column(Float, nullable=False, default=0)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    attempt: Mapped["CertAttempt"] = relationship("CertAttempt", back_populates="responses")
    question: Mapped["CertQuestion"] = relationship("CertQuestion")
