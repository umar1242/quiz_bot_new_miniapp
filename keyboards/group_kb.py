"""
keyboards/group_kb.py
Inline-клавиатуры для группового режима квиза.
"""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from utils.i18n import t


def join_kb(session_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """Кнопка 'Присоединиться' для группового квиза."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t("kb.join", lang),
            callback_data=f"join:{session_id}",
        )],
        [InlineKeyboardButton(
            text=t("kb.start_group", lang),
            callback_data=f"start_group:{session_id}",
        )],
    ])


def joined_kb(session_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """Кнопка после того как пользователь уже присоединился."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t("kb.joined", lang),
            callback_data=f"already_joined:{session_id}",
        )],
    ])
