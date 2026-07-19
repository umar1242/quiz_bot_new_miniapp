"""
services/flashcard_parser.py
Парсер флешкарт. Формат (в .txt / .docx / .pdf):

    Лицевая сторона карточки 1
    ===
    #Правильный оборот (true)
    ===
    Подменённый, но правдоподобный оборот (false)
    +++
    Лицевая сторона карточки 2
    ===
    Оборотная сторона
    +++
    ...

  +++  (на отдельной строке) — разделяет карточки между собой
  ===  (на отдельной строке) — разделяет стороны карточки (лицо и обороты)
  #    — ставится перед ПРАВИЛЬНЫМ оборотом (как правильный ответ в квизах)

У карточки может быть один оборот (тогда он и есть правильный) или два:
правильный, помеченный #, и ложный. Ложный оборот используется в режиме
«Верно/Неверно» вместо подстановки чужого оборота.

Текст из файла извлекается существующими конвертерами (txt/docx/pdf),
а здесь только режется по разделителям.
"""
import re

from dto.quiz_dto import FlashcardDTO
from services.parser import extract_text

# Разделители — три и более символа на отдельной строке (допускаем пробелы вокруг)
CARD_SEP = re.compile(r'^\s*\+{3,}\s*$', re.MULTILINE)   # +++ между карточками
SIDE_SEP = re.compile(r'^\s*={3,}\s*$',  re.MULTILINE)   # === между сторонами карточки

CORRECT_MARK = '#'   # помечает правильный (true) оборот — как в парсере квизов


async def parse_flashcards(filename: str, file_bytes: bytes) -> list[FlashcardDTO]:
    """Файл → текст → список FlashcardDTO. Бросает ValueError если формат не распознан."""
    text = await extract_text(filename, file_bytes)
    return parse_flashcards_text(text)


def parse_flashcards_text(text: str) -> list[FlashcardDTO]:
    """Разбирает plain text по шаблону +++ / ===."""
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    cards: list[FlashcardDTO] = []
    for block in CARD_SEP.split(text):
        block = block.strip()
        if not block:
            continue

        sides = [s.strip() for s in SIDE_SEP.split(block) if s.strip()]
        if len(sides) < 2:
            # Нет разделителя === внутри карточки — пропускаем
            continue

        front = sides[0]
        backs = sides[1:]

        # Определяем правильный (true) оборот и ложный (false):
        #   • оборот с # → правильный (ведущие # срезаем);
        #   • если # нигде нет — правильным считаем первый оборот (back-compat);
        #   • первый оборот, не являющийся правильным → ложный; иначе ложного нет.
        back = None
        false_backs: list[str] = []
        for raw in backs:
            if raw.startswith(CORRECT_MARK):
                marked = raw.lstrip(CORRECT_MARK).strip()
                if back is None and marked:
                    back = marked
                elif marked:
                    false_backs.append(marked)
            else:
                false_backs.append(raw)

        if back is None:
            back = false_backs.pop(0) if false_backs else None

        back_false = false_backs[0] if false_backs else None

        # Карточка валидна только если есть И правильный, И ложный оборот.
        # Карточки с одним оборотом (только правильный ответ) отбрасываем.
        if front and back and back_false:
            cards.append(FlashcardDTO(front=front, back=back, back_false=back_false))

    if not cards:
        raise ValueError(
            "Не удалось найти ни одной подходящей карточки.\n"
            "У каждой карточки должно быть ДВА оборота: правильный (с # в начале) "
            "и ложный.\n\n"
            "Формат:\n"
            "Название\n===\n#Правильный оборот\n===\nЛожный оборот\n+++\n"
            "следующая карточка…\n\n"
            "• === (на отдельной строке) разделяет стороны карточки\n"
            "• +++ (на отдельной строке) разделяет карточки\n"
            "• # ставится перед правильным оборотом"
        )

    return cards
