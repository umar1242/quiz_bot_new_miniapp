"""
keyboards/settings_kb.py
Клавиатуры выбора языка и настроек.
"""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from utils.i18n import LANG_NAMES, t


def language_kb(prefix: str = "setlang") -> InlineKeyboardMarkup:
    """
    Кнопки выбора языка: 🇷🇺 Русский | 🇺🇿 O'zbek
    prefix — префикс callback_data ('setlang' при первом выборе, 'chlang' из настроек).
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=LANG_NAMES["ru"], callback_data=f"{prefix}:ru"),
            InlineKeyboardButton(text=LANG_NAMES["uz"], callback_data=f"{prefix}:uz"),
        ]
    ])


def settings_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """Меню настроек."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("settings.btn_language", lang), callback_data="settings:lang")],
    ])
