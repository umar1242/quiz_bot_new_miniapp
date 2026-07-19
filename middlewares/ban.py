"""
middlewares/ban.py
Глобальная блокировка: апдейты от забаненных пользователей молча игнорируются.
Регистрируется ПОСЛЕ DbSessionMiddleware — нужен доступ к data["db"].
Админы (settings.ADMIN_IDS) под бан не попадают никогда.
"""
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, TelegramObject

from config import settings
from services.user_service import is_banned


class BanMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        db = data.get("db")
        if user is not None and db is not None and user.id not in settings.admin_ids:
            if await is_banned(db, user.id):
                if isinstance(event, CallbackQuery):
                    await event.answer("🚫 Вы заблокированы.", show_alert=True)
                return None
        return await handler(event, data)
