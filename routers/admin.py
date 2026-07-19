"""
routers/admin.py
Глобальная админ-панель (только для ADMIN_IDS).

Разделы: 📊 статистика бота, 🔍 квизы, 📇 колоды, 📢 рассылка, 🚫 баны.
"""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from filters.is_admin import IsAdmin
from keyboards.admin_kb import (
    AdminCB, BanCB, BroadcastCB, DeckAdminCB, QuizAdminCB,
    admin_menu, back_menu, ban_toggle_kb, broadcast_confirm_kb,
    deck_delete_confirm_kb, deck_detail_kb, deck_list_kb,
    quiz_delete_confirm_kb, quiz_detail_kb, quiz_list_kb, stats_menu,
)
from services import admin_service, user_service
from services.flashcard_service import get_deck

import db.models as _m  # noqa — side-effect

logger = logging.getLogger(__name__)

router = Router(name="admin")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

BROADCAST_DELAY = 0.05

MENU_TEXT = "🛠 <b>Админ-панель</b>\nВыберите раздел:"


class AdminFSM(StatesGroup):
    search_quiz    = State()
    search_deck    = State()
    broadcast_msg  = State()
    broadcast_confirm = State()
    ban_user       = State()


# --- Меню ----------------------------------------------------------------

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(MENU_TEXT, reply_markup=admin_menu())


@router.callback_query(AdminCB.filter(F.action == "menu"))
async def back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(MENU_TEXT, reply_markup=admin_menu())
    await callback.answer()


# --- Статистика ----------------------------------------------------------

@router.callback_query(AdminCB.filter(F.action == "stats"))
async def show_stats(callback: CallbackQuery, db: AsyncSession) -> None:
    s = await admin_service.bot_stats(db)
    text = (
        "📊 <b>Статистика бота</b>\n"
        f"<i>обновлено {s.generated_at:%H:%M:%S}</i>\n\n"

        "🟢 <b>Сейчас в эфире</b>\n"
        f"   ▶️ Идёт игр: <b>{s.sessions_active}</b>\n"
        f"   ⏳ Лобби ждут: <b>{s.sessions_waiting}</b>\n\n"

        "📈 <b>За последние 24 часа</b>\n"
        f"   🆕 Новых квизов: <b>{s.quizzes_24h}</b>\n"
        f"   🎮 Запущено игр: <b>{s.sessions_24h}</b>\n"
        f"   ✍️ Ответов: <b>{s.answers_24h}</b>\n\n"

        "👤 <b>Пользователи</b>\n"
        f"   Всего: <b>{s.users_total}</b>  ·  🚫 забанено: <b>{s.users_banned}</b>\n\n"

        "📚 <b>Квизы</b>\n"
        f"   Квизов: <b>{s.quizzes_total}</b>  ·  ❓ вопросов: <b>{s.questions_total}</b>\n"
        f"   ⌀ в среднем: <b>{s.avg_questions:.1f}</b> вопр./квиз\n\n"

        "📇 <b>Флешкарты</b>\n"
        f"   Колод: <b>{s.decks_total}</b>  ·  🃏 карточек: <b>{s.cards_total}</b>\n\n"

        "🕹 <b>Игры за всё время</b>\n"
        f"   Сессий: <b>{s.sessions_total}</b>  ·  ✅ завершено: <b>{s.sessions_finished}</b>\n"
        f"   Режимы: 👤 solo <b>{s.sessions_solo}</b>  ·  👥 group <b>{s.sessions_group}</b>\n"
        f"   ✍️ Ответов всего: <b>{s.answers_total}</b>"
    )
    try:
        await callback.message.edit_text(text, reply_markup=stats_menu())
    except TelegramBadRequest:
        pass
    await callback.answer("Обновлено ✅")


# --- Квизы ---------------------------------------------------------------

@router.callback_query(AdminCB.filter(F.action == "quizzes"))
async def show_quizzes(callback: CallbackQuery, state: FSMContext, db: AsyncSession) -> None:
    await state.set_state(AdminFSM.search_quiz)
    quizzes = await admin_service.recent_quizzes(db)
    text = "🔍 <b>Квизы</b>\nПоследние квизы ниже, или пришлите текст/ID для поиска:"
    if not quizzes:
        text = "🔍 <b>Квизы</b>\nПока нет ни одного квиза."
    await callback.message.edit_text(text, reply_markup=quiz_list_kb(quizzes))
    await callback.answer()


@router.message(AdminFSM.search_quiz, F.text)
async def search_quizzes(message: Message, db: AsyncSession) -> None:
    quizzes = await admin_service.search_quizzes(db, message.text)
    if not quizzes:
        await message.answer("Ничего не найдено.", reply_markup=back_menu())
        return
    await message.answer(f"Найдено: {len(quizzes)}", reply_markup=quiz_list_kb(quizzes))


@router.callback_query(QuizAdminCB.filter(F.action == "view"))
async def view_quiz(callback: CallbackQuery, callback_data: QuizAdminCB, db: AsyncSession) -> None:
    from services.quiz_service import get_quiz
    quiz = await get_quiz(db, callback_data.quiz_id)
    if quiz is None:
        await callback.answer("Квиз не найден", show_alert=True)
        return
    text = (
        f"📋 <b>{quiz.title}</b>\n\n"
        f"🆔 ID: <code>{quiz.id}</code>\n"
        f"👤 Владелец: <code>{quiz.owner_id}</code>\n"
        f"❓ Вопросов: <b>{len(quiz.questions)}</b>\n"
        f"⏱ Таймер: {quiz.timer_sec} сек\n"
        f"🔀 Вопросы: {'перемешиваются' if quiz.shuffle_q else 'по порядку'}, "
        f"ответы: {'перемешиваются' if quiz.shuffle_a else 'по порядку'}\n"
        f"📅 Создан: {quiz.created_at:%Y-%m-%d %H:%M}"
    )
    await callback.message.edit_text(text, reply_markup=quiz_detail_kb(quiz.id))
    await callback.answer()


@router.callback_query(QuizAdminCB.filter(F.action == "delete"))
async def delete_quiz_ask(callback: CallbackQuery, callback_data: QuizAdminCB) -> None:
    await callback.message.edit_text(
        "⚠️ Удалить квиз безвозвратно? Все вопросы и сессии тоже удалятся.",
        reply_markup=quiz_delete_confirm_kb(callback_data.quiz_id),
    )
    await callback.answer()


@router.callback_query(QuizAdminCB.filter(F.action == "confirm_delete"))
async def delete_quiz_confirm(callback: CallbackQuery, callback_data: QuizAdminCB, db: AsyncSession) -> None:
    from services.quiz_service import get_quiz
    quiz = await get_quiz(db, callback_data.quiz_id)
    if quiz is not None:
        await admin_service.delete_quiz(db, quiz)
    await callback.answer("Квиз удалён")
    quizzes = await admin_service.recent_quizzes(db)
    await callback.message.edit_text("🗑 Квиз удалён.\n🔍 <b>Квизы</b>:", reply_markup=quiz_list_kb(quizzes))


# --- Колоды --------------------------------------------------------------

@router.callback_query(AdminCB.filter(F.action == "decks"))
async def show_decks(callback: CallbackQuery, state: FSMContext, db: AsyncSession) -> None:
    await state.set_state(AdminFSM.search_deck)
    decks = await admin_service.recent_decks(db)
    text = "📇 <b>Колоды</b>\nПоследние колоды ниже, или пришлите текст/ID для поиска:"
    if not decks:
        text = "📇 <b>Колоды</b>\nПока нет ни одной колоды."
    await callback.message.edit_text(text, reply_markup=deck_list_kb(decks))
    await callback.answer()


@router.message(AdminFSM.search_deck, F.text)
async def search_decks(message: Message, db: AsyncSession) -> None:
    decks = await admin_service.search_decks(db, message.text)
    if not decks:
        await message.answer("Ничего не найдено.", reply_markup=back_menu())
        return
    await message.answer(f"Найдено: {len(decks)}", reply_markup=deck_list_kb(decks))


@router.callback_query(DeckAdminCB.filter(F.action == "view"))
async def view_deck(callback: CallbackQuery, callback_data: DeckAdminCB, db: AsyncSession) -> None:
    deck = await get_deck(db, callback_data.deck_id)
    if deck is None:
        await callback.answer("Колода не найдена", show_alert=True)
        return
    from utils.deeplink import make_deck_link
    text = (
        f"📇 <b>{deck.title}</b>\n\n"
        f"🆔 ID: <code>{deck.id}</code>\n"
        f"👤 Владелец: <code>{deck.owner_id}</code>\n"
        f"🃏 Карточек: <b>{len(deck.cards)}</b>\n"
        f"📅 Создана: {deck.created_at:%Y-%m-%d %H:%M}\n\n"
        f"🔗 {make_deck_link(deck.id)}"
    )
    await callback.message.edit_text(text, reply_markup=deck_detail_kb(deck.id))
    await callback.answer()


@router.callback_query(DeckAdminCB.filter(F.action == "delete"))
async def delete_deck_ask(callback: CallbackQuery, callback_data: DeckAdminCB) -> None:
    await callback.message.edit_text(
        "⚠️ Удалить колоду безвозвратно? Все карточки тоже удалятся.",
        reply_markup=deck_delete_confirm_kb(callback_data.deck_id),
    )
    await callback.answer()


@router.callback_query(DeckAdminCB.filter(F.action == "confirm_delete"))
async def delete_deck_confirm(callback: CallbackQuery, callback_data: DeckAdminCB, db: AsyncSession) -> None:
    deck = await get_deck(db, callback_data.deck_id)
    if deck is not None:
        await admin_service.delete_deck_admin(db, deck)
    await callback.answer("Колода удалена")
    decks = await admin_service.recent_decks(db)
    await callback.message.edit_text("🗑 Колода удалена.\n📇 <b>Колоды</b>:", reply_markup=deck_list_kb(decks))


# --- Рассылка ------------------------------------------------------------

@router.callback_query(AdminCB.filter(F.action == "broadcast"))
async def broadcast_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminFSM.broadcast_msg)
    await callback.message.edit_text(
        "📢 Пришлите сообщение для рассылки (текст, фото, видео — что угодно).",
        reply_markup=back_menu(),
    )
    await callback.answer()


@router.message(AdminFSM.broadcast_msg)
async def broadcast_preview(message: Message, state: FSMContext) -> None:
    await state.update_data(from_chat_id=message.chat.id, message_id=message.message_id)
    await state.set_state(AdminFSM.broadcast_confirm)
    await message.answer(
        "👆 Это сообщение будет разослано всем пользователям. Подтвердить?",
        reply_markup=broadcast_confirm_kb(),
    )


@router.callback_query(AdminFSM.broadcast_confirm, BroadcastCB.filter(F.action == "cancel"))
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Рассылка отменена.", reply_markup=back_menu())
    await callback.answer()


@router.callback_query(AdminFSM.broadcast_confirm, BroadcastCB.filter(F.action == "confirm"))
async def broadcast_run(callback: CallbackQuery, state: FSMContext, db: AsyncSession, bot: Bot) -> None:
    data = await state.get_data()
    await state.clear()
    from_chat_id = data["from_chat_id"]
    message_id   = data["message_id"]

    user_ids = await user_service.active_user_ids(db)
    await callback.message.edit_text(f"📤 Рассылка запущена для {len(user_ids)} польз…")
    await callback.answer()

    sent = failed = 0
    for uid in user_ids:
        try:
            await bot.copy_message(chat_id=uid, from_chat_id=from_chat_id, message_id=message_id)
            sent += 1
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            try:
                await bot.copy_message(chat_id=uid, from_chat_id=from_chat_id, message_id=message_id)
                sent += 1
            except Exception:
                failed += 1
        except Exception:
            failed += 1
        await asyncio.sleep(BROADCAST_DELAY)

    await bot.send_message(
        callback.message.chat.id,
        f"✅ Рассылка завершена.\nОтправлено: <b>{sent}</b>, не доставлено: <b>{failed}</b>",
        reply_markup=back_menu(),
    )


# --- Баны ----------------------------------------------------------------

@router.callback_query(AdminCB.filter(F.action == "bans"))
async def bans_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminFSM.ban_user)
    await callback.message.edit_text(
        "🚫 <b>Баны</b>\nПришлите <b>user_id</b> пользователя для бана/разбана.",
        reply_markup=back_menu(),
    )
    await callback.answer()


@router.message(AdminFSM.ban_user, F.text)
async def ban_lookup(message: Message, db: AsyncSession) -> None:
    raw = message.text.strip()
    if not raw.lstrip("-").isdigit():
        await message.answer("Нужен числовой user_id.", reply_markup=back_menu())
        return
    user_id = int(raw)
    banned = await user_service.is_banned(db, user_id)
    status = "🚫 <b>забанен</b>" if banned else "🟢 <b>не забанен</b>"
    await message.answer(
        f"Пользователь <code>{user_id}</code>: {status}",
        reply_markup=ban_toggle_kb(user_id, banned),
    )


@router.callback_query(BanCB.filter(F.action == "toggle"))
async def ban_toggle(callback: CallbackQuery, callback_data: BanCB, db: AsyncSession) -> None:
    user_id = callback_data.user_id
    new_banned = not await user_service.is_banned(db, user_id)
    await user_service.set_banned(db, user_id, new_banned)
    status = "🚫 <b>забанен</b>" if new_banned else "🟢 <b>разбанен</b>"
    await callback.message.edit_text(
        f"Пользователь <code>{user_id}</code>: {status}",
        reply_markup=ban_toggle_kb(user_id, new_banned),
    )
    await callback.answer("Готово")
