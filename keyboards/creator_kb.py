"""
keyboards/creator_kb.py
Inline-клавиатуры для флоу создания и настройки квиза.
"""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.i18n import t


# ---------------------------------------------------------------------------
# Настройка таймера
# ---------------------------------------------------------------------------

TIMER_OPTIONS = [5, 10, 15, 20, 30, 45, 60, 90, 120]
PRACTICE_TIMER = 0   # специальное значение — практика без таймера


def timer_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """Выбор таймера на вопрос."""
    builder = InlineKeyboardBuilder()
    for sec in TIMER_OPTIONS:
        label = t("sec", lang, n=sec) if sec < 60 else t("min", lang, n=sec // 60)
        builder.button(text=label, callback_data=f"timer:{sec}")
    # Режим практики — без таймера
    builder.button(text=t("kb.timer_practice", lang), callback_data=f"timer:{PRACTICE_TIMER}")
    builder.adjust(3)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Порядок вопросов
# ---------------------------------------------------------------------------

def order_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t("kb.order_fixed", lang),   callback_data="order:fixed"),
            InlineKeyboardButton(text=t("kb.order_shuffle", lang), callback_data="order:shuffle"),
        ]
    ])


# ---------------------------------------------------------------------------
# Перемешивание ответов
# ---------------------------------------------------------------------------

def shuffle_answers_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t("kb.order_fixed", lang),   callback_data="shuffle_a:fixed"),
            InlineKeyboardButton(text=t("kb.order_shuffle", lang), callback_data="shuffle_a:shuffle"),
        ]
    ])


# ---------------------------------------------------------------------------
# Подтверждение сохранения
# ---------------------------------------------------------------------------

def confirm_save_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t("kb.save", lang),       callback_data="save:confirm"),
            InlineKeyboardButton(text=t("common.cancel", lang), callback_data="save:cancel"),
        ]
    ])


# ---------------------------------------------------------------------------
# Разбивка на части (показывается если вопросов > SPLIT_THRESHOLD)
# ---------------------------------------------------------------------------

SPLIT_THRESHOLD = 50   # порог после которого предлагаем разбивку
SPLIT_OPTIONS   = [25, 50, 100]  # варианты размера части


def split_kb(total: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """
    Клавиатура выбора размера части.
    Показываем только варианты меньше total (нет смысла делить на части >= всего).
    """
    builder = InlineKeyboardBuilder()
    for n in SPLIT_OPTIONS:
        if n < total:
            parts = (total + n - 1) // n  # ceil division
            builder.button(
                text=t("kb.split_by", lang, n=n, parts=parts),
                callback_data=f"split:{n}",
            )
    builder.button(text=t("kb.split_keep_all", lang, total=total), callback_data="split:0")
    builder.adjust(1)
    return builder.as_markup()
