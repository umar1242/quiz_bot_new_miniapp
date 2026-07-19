"""
keyboards/deck_kb.py
Inline-клавиатуры для флешкарт: список колод, меню колоды, режим обучения.
"""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.models import Deck
from utils.i18n import t


def decks_list_kb(decks: list[Deck], lang: str = "ru") -> InlineKeyboardMarkup:
    """Список колод пользователя + кнопка создания."""
    builder = InlineKeyboardBuilder()
    for d in decks:
        title = d.title[:35] + "…" if len(d.title) > 35 else d.title
        builder.button(text=f"📇 {title}", callback_data=f"deck:open:{d.id}")
    builder.button(text=t("deck.kb_create", lang), callback_data="deck:create")
    builder.adjust(1)
    return builder.as_markup()


def deck_view_kb(deck_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """Меню колоды (владелец): учить / тест / поделиться / удалить / назад."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("deck.kb_study", lang),    callback_data=f"deck:study:{deck_id}")],
        [InlineKeyboardButton(text=t("deck.kb_tf", lang),       callback_data=f"deck:tf:{deck_id}")],
        [InlineKeyboardButton(text=t("deck.kb_share", lang),    callback_data=f"deck:share:{deck_id}")],
        [InlineKeyboardButton(text=t("deck.kb_delete", lang),   callback_data=f"deck:delete:{deck_id}")],
        [InlineKeyboardButton(text=t("deck.kb_back_list", lang), callback_data="deck:list")],
    ])


def deck_shared_view_kb(deck_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """Меню колоды по ссылке (любой пользователь): только учить / тест."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("deck.kb_study", lang), callback_data=f"deck:study:{deck_id}")],
        [InlineKeyboardButton(text=t("deck.kb_tf", lang),    callback_data=f"deck:tf:{deck_id}")],
    ])


def confirm_delete_deck_kb(deck_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """Подтверждение удаления колоды."""
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t("deck.kb_confirm_delete", lang), callback_data=f"deck:delete_yes:{deck_id}"),
        InlineKeyboardButton(text=t("common.cancel", lang),          callback_data=f"deck:open:{deck_id}"),
    ]])


def study_show_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """Кнопка «Показать ответ» (лицо карточки)."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("deck.kb_show", lang), callback_data="study:show")],
        [InlineKeyboardButton(text=t("deck.kb_stop", lang), callback_data="study:stop")],
    ])


def study_grade_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """Кнопки оценки «Знаю / Не знаю» (после показа оборота)."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t("deck.kb_know", lang),     callback_data="study:know"),
            InlineKeyboardButton(text=t("deck.kb_dontknow", lang), callback_data="study:dontknow"),
        ],
        [InlineKeyboardButton(text=t("deck.kb_stop", lang), callback_data="study:stop")],
    ])


def study_done_kb(deck_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """Кнопки после завершения обучения: ещё раз / к колоде."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("deck.kb_again", lang),     callback_data=f"deck:study:{deck_id}")],
        [InlineKeyboardButton(text=t("deck.kb_back_deck", lang), callback_data=f"deck:open:{deck_id}")],
    ])


def tf_control_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """Управляющее сообщение режима «Верно/Неверно» — кнопка остановки."""
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t("deck.kb_stop", lang), callback_data="tf:stop"),
    ]])


def tf_done_kb(deck_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """Кнопки после завершения теста: ещё раунд / к колоде."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("deck.kb_tf_again", lang), callback_data=f"deck:tf:{deck_id}")],
        [InlineKeyboardButton(text=t("deck.kb_back_deck", lang), callback_data=f"deck:open:{deck_id}")],
    ])
