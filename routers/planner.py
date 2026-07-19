"""
routers/planner.py
Команда /planner — открывает Mini App «Учебный план».
Плюс колбэки подтверждения регистрации задания (deep link pi_<item_id>):
пользователь запускает задание из планера → бот показывает условия → по кнопке
запускает квиз/тест «с регистрацией» (результат зачтётся только при полном прохождении).
"""
import html

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)
from sqlalchemy.ext.asyncio import AsyncSession

from webapp import runtime

router = Router()


@router.message(Command("planner"))
async def cmd_planner(message: Message) -> None:
    url = runtime.get_webapp_url()
    if not url:
        await message.answer(
            "📊 Планер пока не настроен: нет публичного HTTPS-адреса Mini App. "
            "Включи туннель (TUNNEL_ENABLED=true) или задай WEBAPP_URL в .env."
        )
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📊 Открыть планер", web_app=WebAppInfo(url=url))
    ]])
    await message.answer(
        "🌿 <b>Учебный план</b>\n\n"
        "Выбери период и задания (квизы, колоды), укажи сколько раз пройти каждое — "
        "и отслеживай прогресс: сколько пройдено, сколько правильных ответов.\n\n"
        "⚠️ Прохождение засчитывается, только если запускать задание "
        "<b>из планера</b> (кнопка ▶) и доходить <b>до конца</b>.\n\n"
        "Нажми кнопку ниже 👇",
        reply_markup=kb,
    )


# ---------------------------------------------------------------------------
# Регистрация задания плана
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "plreg:cancel")
async def cb_reg_cancel(call: CallbackQuery) -> None:
    await call.message.edit_text(
        "✖️ Отменено. Задание не запущено и не будет засчитано в план."
    )
    await call.answer()


@router.callback_query(F.data.startswith("plreg:start:"))
async def cb_reg_start(call: CallbackQuery, db: AsyncSession, lang: str) -> None:
    item_id = int(call.data.split(":")[2])
    from services.planner_service import get_plan_item
    item = await get_plan_item(db, call.from_user.id, item_id)
    if item is None:
        await call.answer("Задание не найдено", show_alert=True)
        return

    await call.message.edit_text(
        f"✅ Запускаю с регистрацией: <b>{html.escape(item.title)}</b>.\n"
        "Пройди до конца, чтобы прохождение зачлось в план! 💪"
    )
    await call.answer()

    if item.kind == "quiz":
        from routers.start import launch_registered_quiz
        await launch_registered_quiz(
            call.bot, db, call.message.chat.id, call.from_user, item.ref_id, item.id, lang
        )
    elif item.kind == "tf":
        from routers.deck import launch_registered_tf
        await launch_registered_tf(
            call.bot, db, call.message.chat.id, call.from_user, item.ref_id, item.id, lang
        )
