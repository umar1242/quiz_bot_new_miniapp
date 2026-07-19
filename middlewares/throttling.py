"""
middlewares/throttling.py
Rate limiting: не более 1 запроса в THROTTLE_RATE секунд на пользователя.
Использует Redis с TTL — если ключ существует, апдейт игнорируется.
"""
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from redis_client import RedisKeys, redis

THROTTLE_RATE = 0.5  # секунд между разрешёнными сообщениями


class ThrottlingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Работаем только с Message (callback_query — не троттлим)
        if not isinstance(event, Message):
            return await handler(event, data)

        user = event.from_user
        if user is None:
            return await handler(event, data)

        key = RedisKeys.user_throttle(user.id)

        # SET NX = установить только если ключ не существует
        # Если вернул True — первый запрос в окне, пропускаем
        # Если вернул None — ключ уже был, значит флуд — игнорируем
        set_result = await redis.set(key, "1", px=int(THROTTLE_RATE * 1000), nx=True)

        if set_result is None:
            # Молча игнорируем — не отвечаем пользователю
            return None

        return await handler(event, data)
