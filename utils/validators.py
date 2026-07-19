"""
utils/validators.py
Валидация QuestionDTO перед сохранением в БД.
Проверяет ограничения Telegram Poll API.
"""
from dto.quiz_dto import QuestionDTO
from utils.i18n import t

# Лимиты Telegram Poll API
# MAX_QUESTION_LEN убран — длинные вопросы отправляются отдельным сообщением перед поллом
MAX_ANSWER_LEN   = 100   # лимит самого Telegram для poll options
MIN_ANSWERS      = 2
MAX_ANSWERS      = 10

# Если ответ длиннее этого — он будет показан в тексте вопроса, а в poll пойдут метки A/B/C/D
LONG_ANSWER_THRESHOLD = 100


class ValidationError(Exception):
    """Ошибка валидации с номером вопроса и описанием."""
    def __init__(self, question_num: int, reason: str):
        self.question_num = question_num
        self.reason = reason
        super().__init__(f"Вопрос {question_num}: {reason}")


def validate_question(q: QuestionDTO, num: int, lang: str = "ru") -> None:
    """Бросает ValidationError если вопрос не прошёл проверку."""

    if not q.text.strip():
        raise ValidationError(num, t("val.empty_text", lang))

    # Длинные вопросы НЕ блокируем — они будут отправлены отдельным сообщением перед поллом

    if len(q.answers) < MIN_ANSWERS:
        raise ValidationError(num, t("val.too_few", lang, n=len(q.answers), min=MIN_ANSWERS))

    if len(q.answers) > MAX_ANSWERS:
        raise ValidationError(num, t("val.too_many", lang, n=len(q.answers), max=MAX_ANSWERS))

    correct_count = sum(1 for a in q.answers if a.is_correct)
    if correct_count == 0:
        raise ValidationError(num, t("val.no_correct", lang))
    if correct_count > 1:
        raise ValidationError(num, t("val.many_correct", lang, n=correct_count))

    for i, answer in enumerate(q.answers, start=1):
        if not answer.text.strip():
            raise ValidationError(num, t("val.empty_variant", lang, i=i))
        # Длинные ответы НЕ блокируем — они будут показаны в тексте вопроса


def validate_questions(questions: list[QuestionDTO], lang: str = "ru") -> list[str]:
    """
    Проверяет все вопросы.
    Возвращает список строк с ошибками (пустой список = всё ок).
    Не бросает исключение — чтобы показать пользователю все ошибки сразу.
    """
    errors: list[str] = []
    for i, q in enumerate(questions, start=1):
        try:
            validate_question(q, i, lang)
        except ValidationError as e:
            errors.append(t("val.question_prefix", lang, num=i, reason=e.reason))
    return errors