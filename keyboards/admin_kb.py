"""
keyboards/admin_kb.py
Клавиатуры и CallbackData-фабрики для глобальной админ-панели.
"""
from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class AdminCB(CallbackData, prefix="adm"):
    action: str   # menu | stats | quizzes | decks | broadcast | bans


class QuizAdminCB(CallbackData, prefix="admq"):
    action: str   # view | delete | confirm_delete
    quiz_id: int


class DeckAdminCB(CallbackData, prefix="admdk"):
    action: str   # view | delete | confirm_delete
    deck_id: int


class BroadcastCB(CallbackData, prefix="admbc"):
    action: str   # confirm | cancel


class BanCB(CallbackData, prefix="admban"):
    action: str   # toggle
    user_id: int


def admin_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Статистика",  callback_data=AdminCB(action="stats"))
    builder.button(text="🔍 Квизы",       callback_data=AdminCB(action="quizzes"))
    builder.button(text="📇 Колоды",      callback_data=AdminCB(action="decks"))
    builder.button(text="📢 Рассылка",    callback_data=AdminCB(action="broadcast"))
    builder.button(text="🚫 Баны",        callback_data=AdminCB(action="bans"))
    builder.adjust(2)
    return builder.as_markup()


def back_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⬅️ В меню", callback_data=AdminCB(action="menu").pack())
    ]])


def stats_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Обновить", callback_data=AdminCB(action="stats"))
    builder.button(text="⬅️ В меню",   callback_data=AdminCB(action="menu"))
    builder.adjust(2)
    return builder.as_markup()


# --- Квизы ---

def quiz_list_kb(quizzes) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for q in quizzes:
        title = q.title if len(q.title) <= 40 else q.title[:39] + "…"
        builder.button(
            text=f"#{q.id} · {title}",
            callback_data=QuizAdminCB(action="view", quiz_id=q.id),
        )
    builder.button(text="⬅️ В меню", callback_data=AdminCB(action="menu"))
    builder.adjust(1)
    return builder.as_markup()


def quiz_detail_kb(quiz_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Удалить",   callback_data=QuizAdminCB(action="delete", quiz_id=quiz_id))
    builder.button(text="⬅️ К квизам", callback_data=AdminCB(action="quizzes"))
    builder.adjust(1)
    return builder.as_markup()


def quiz_delete_confirm_kb(quiz_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, удалить", callback_data=QuizAdminCB(action="confirm_delete", quiz_id=quiz_id))
    builder.button(text="↩️ Отмена",      callback_data=QuizAdminCB(action="view", quiz_id=quiz_id))
    builder.adjust(1)
    return builder.as_markup()


# --- Колоды ---

def deck_list_kb(decks) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for d in decks:
        title = d.title if len(d.title) <= 40 else d.title[:39] + "…"
        builder.button(
            text=f"#{d.id} · {title}",
            callback_data=DeckAdminCB(action="view", deck_id=d.id),
        )
    builder.button(text="⬅️ В меню", callback_data=AdminCB(action="menu"))
    builder.adjust(1)
    return builder.as_markup()


def deck_detail_kb(deck_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Удалить",   callback_data=DeckAdminCB(action="delete", deck_id=deck_id))
    builder.button(text="⬅️ К колодам", callback_data=AdminCB(action="decks"))
    builder.adjust(1)
    return builder.as_markup()


def deck_delete_confirm_kb(deck_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, удалить", callback_data=DeckAdminCB(action="confirm_delete", deck_id=deck_id))
    builder.button(text="↩️ Отмена",      callback_data=DeckAdminCB(action="view", deck_id=deck_id))
    builder.adjust(1)
    return builder.as_markup()


# --- Рассылка ---

def broadcast_confirm_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Разослать", callback_data=BroadcastCB(action="confirm"))
    builder.button(text="↩️ Отмена",    callback_data=BroadcastCB(action="cancel"))
    builder.adjust(2)
    return builder.as_markup()


# --- Баны ---

def ban_toggle_kb(user_id: int, is_banned: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if is_banned:
        builder.button(text="✅ Разбанить", callback_data=BanCB(action="toggle", user_id=user_id))
    else:
        builder.button(text="🚫 Забанить",  callback_data=BanCB(action="toggle", user_id=user_id))
    builder.button(text="⬅️ В меню", callback_data=AdminCB(action="menu"))
    builder.adjust(1)
    return builder.as_markup()
