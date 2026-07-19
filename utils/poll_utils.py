LABELS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]

# Telegram Quiz Poll: макс длина текста вопроса
POLL_QUESTION_LIMIT = 255


def build_poll_data(question, answers):
    """
    Формирует (question_text, options) для send_poll.
    Если текст вопроса > POLL_QUESTION_LIMIT — обрезает до лимита,
    полный текст нужно отправить отдельным сообщением через send_question_with_poll.
    """
    has_long_answers = any(len(a.text) > 100 for a in answers)

    if has_long_answers:
        options_block = "\n".join(
            f"{LABELS[i]}) {a.text}" for i, a in enumerate(answers)
        )
        full_text = f"{question.text}\n\n{options_block}"
        question_text = full_text[:POLL_QUESTION_LIMIT]
        options = [LABELS[i] for i in range(len(answers))]
    else:
        question_text = question.text[:POLL_QUESTION_LIMIT]
        options = [a.text[:100] for a in answers]

    return question_text, options


def needs_long_message(question, answers) -> bool:
    """
    Возвращает True если текст вопроса + ответы не вмещаются в poll
    и нужно отправить отдельное сообщение перед поллом.
    """
    has_long_answers = any(len(a.text) > 100 for a in answers)
    if has_long_answers:
        options_block = "\n".join(
            f"{LABELS[i]}) {a.text}" for i, a in enumerate(answers)
        )
        full_text = f"{question.text}\n\n{options_block}"
    else:
        full_text = question.text

    return len(full_text) > POLL_QUESTION_LIMIT


async def maybe_send_long_question(chat_id: int, question, answers, bot) -> None:
    """
    Если текст вопроса не помещается в poll — отправляет его отдельным сообщением.
    Вызывать ПЕРЕД send_poll.
    """
    if not needs_long_message(question, answers):
        return

    has_long_answers = any(len(a.text) > 100 for a in answers)

    if has_long_answers:
        options_block = "\n".join(
            f"{LABELS[i]}) {a.text}" for i, a in enumerate(answers)
        )
        full_text = f"<b>{question.text}</b>\n\n{options_block}"
    else:
        full_text = f"<b>{question.text}</b>"

    await bot.send_message(chat_id, full_text)
