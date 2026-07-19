"""
dto/quiz_dto.py
Промежуточные структуры данных между парсером → сервисом → БД.
Не содержат ORM, можно использовать и тестировать независимо.
"""
from dataclasses import dataclass, field


@dataclass
class AnswerDTO:
    text: str
    is_correct: bool


@dataclass
class QuestionDTO:
    text: str
    answers: list[AnswerDTO] = field(default_factory=list)
    explanation: str | None = None  # опциональное объяснение после ответа


@dataclass
class QuizCreateDTO:
    """Полный квиз готовый к сохранению в БД."""
    owner_id: int
    title: str
    questions: list[QuestionDTO] = field(default_factory=list)
    timer_sec: int = 30
    shuffle_q: bool = False
    shuffle_a: bool = False


@dataclass
class FlashcardDTO:
    """Одна флешкарта: лицо и оборот.

    back        — правильный оборот (показывается в режиме обучения).
    back_false  — заведомо ложный оборот для режима «Верно/Неверно».
                  None, если в файле для карточки указан только один оборот.
    """
    front: str
    back: str
    back_false: str | None = None


@dataclass
class DeckCreateDTO:
    """Колода флешкарт готовая к сохранению в БД."""
    owner_id: int
    title: str
    cards: list[FlashcardDTO] = field(default_factory=list)
