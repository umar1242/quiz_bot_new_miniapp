"""
utils/deeplink.py
Генерация и парсинг deep link для квизов.

Формат: https://t.me/BOT_USERNAME?start=quiz_QUIZID
Параметр start передаётся боту как аргумент команды /start.
"""
from config import settings


def make_quiz_link(quiz_id: int) -> str:
    """Возвращает deep link для квиза."""
    return f"https://t.me/{settings.BOT_USERNAME}?start=quiz_{quiz_id}"


def make_group_quiz_link(quiz_id: int) -> str:
    return f"https://t.me/{settings.BOT_USERNAME}?startgroup=quiz_{quiz_id}"


def make_deck_link(deck_id: int) -> str:
    """Возвращает deep link для колоды флешкарт."""
    return f"https://t.me/{settings.BOT_USERNAME}?start=deck_{deck_id}"


def parse_start_param(param: str) -> int | None:
    """
    Разбирает аргумент /start для квизов.
    Возвращает quiz_id (int) или None если параметр не наш.
    """
    if not param or not param.startswith("quiz_"):
        return None
    raw = param[len("quiz_"):]
    try:
        return int(raw)
    except ValueError:
        return None


def parse_deck_start_param(param: str) -> int | None:
    """Разбирает аргумент /start для колод. Возвращает deck_id или None."""
    if not param or not param.startswith("deck_"):
        return None
    raw = param[len("deck_"):]
    try:
        return int(raw)
    except ValueError:
        return None


def make_plan_item_link(item_id: int) -> str:
    """Deep link для запуска задания плана «с регистрацией»."""
    return f"https://t.me/{settings.BOT_USERNAME}?start=pi_{item_id}"


def parse_plan_item_param(param: str) -> int | None:
    """Разбирает аргумент /start для регистрируемого задания плана. Возвращает plan_item_id или None."""
    if not param or not param.startswith("pi_"):
        return None
    try:
        return int(param[len("pi_"):])
    except ValueError:
        return None
