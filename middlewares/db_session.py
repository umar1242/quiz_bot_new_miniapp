"""
middlewares/db_session.py
Прокидывает AsyncSession в data["db"] каждого хэндлера.
Сессия открывается на время обработки апдейта; коммит делается только если
хэндлер реально что-то записал (SQLAlchemy autoflush + commit on exit).
Используем autobegin (без явного session.begin()) — SQLite откладывает
захват write-lock до первой фактической записи, что снижает конкуренцию.
"""
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from db.base import AsyncSessionFactory


class DbSessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with AsyncSessionFactory() as session:
            data["db"] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
