"""
keyboards/main_kb.py
Постоянная нижняя навигация бота — реплай-клавиатура с эмодзи под полем ввода.
"""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BTN_HOME = "🏠 Меню"
BTN_MYQUIZ = "📚 Мои квизы"
BTN_CERT = "🎓 Сертификат"
BTN_BIO = "🧬 Bio Solver"
BTN_ATF = "⚡ ATF"
BTN_DECKS = "🃏 Колоды"
BTN_SETTINGS = "⚙️ Настройки"


def main_reply_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_HOME), KeyboardButton(text=BTN_MYQUIZ)],
            [KeyboardButton(text=BTN_CERT), KeyboardButton(text=BTN_BIO)],
            [KeyboardButton(text=BTN_ATF), KeyboardButton(text=BTN_DECKS)],
            [KeyboardButton(text=BTN_SETTINGS)],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )
