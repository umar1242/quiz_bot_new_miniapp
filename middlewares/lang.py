"""
middlewares/lang.py
Прокидывает язык интерфейса пользователя в data["lang"].
Регистрируется ПОСЛЕ DbSessionMiddleware — чтобы иметь доступ к data["db"].
"""
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from services.user_service import get_lang
from utils.i18n import DEFAULT_LANG


class LangMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        db = data.get("db")
        if user is not None and db is not None:
            data["lang"] = await get_lang(db, user.id)
        else:
            data["lang"] = DEFAULT_LANG
        return await handler(event, data)
