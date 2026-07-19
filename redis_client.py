"""
redis_client.py
In-memory замена Redis — без внешнего сервера.
Подходит для Android/PRoot, где поднять Redis проблематично.

ВНИМАНИЕ: данные живут только в памяти процесса. При перезапуске бота
всё стирается — для троттлинга, локов и poll-маппинга это нормально,
а долгоживущее состояние и так хранится в SQLite.

Публичный интерфейс (`redis`, `ping`, хелперы, RedisKeys) совместим
со старым кодом, поэтому остальные модули менять не нужно.
"""
from __future__ import annotations

import asyncio
import json
import time
from typing import Any

from config import settings  # noqa: F401  (оставлен для совместимости импортов)


class InMemoryRedis:
    """
    Минималистичная реализация подмножества Redis-команд на dict в памяти.
    Реализованы только методы, которые реально использует бот:
    set/get/delete, sadd/scard/smembers/sismember, expire,
    hset/hgetall, rpush/lrange, ping.
    Поддерживается TTL (ex/px и expire) с ленивым удалением.
    """

    def __init__(self) -> None:
        self._str: dict[str, str] = {}
        self._set: dict[str, set[str]] = {}
        self._hash: dict[str, dict[str, str]] = {}
        self._list: dict[str, list[str]] = {}
        self._expire_at: dict[str, float] = {}
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------ TTL
    def _is_expired(self, key: str) -> bool:
        exp = self._expire_at.get(key)
        if exp is not None and exp <= time.monotonic():
            self._drop(key)
            return True
        return False

    def _drop(self, key: str) -> None:
        self._str.pop(key, None)
        self._set.pop(key, None)
        self._hash.pop(key, None)
        self._list.pop(key, None)
        self._expire_at.pop(key, None)

    def _exists(self, key: str) -> bool:
        if self._is_expired(key):
            return False
        return (
            key in self._str
            or key in self._set
            or key in self._hash
            or key in self._list
        )

    # --------------------------------------------------------------- generic
    async def ping(self) -> bool:
        return True

    async def set(
        self,
        key: str,
        value: Any,
        ex: int | None = None,
        px: int | None = None,
        nx: bool = False,
    ) -> bool | None:
        async with self._lock:
            self._is_expired(key)
            if nx and key in self._str:
                return None
            self._str[key] = str(value)
            if ex is not None:
                self._expire_at[key] = time.monotonic() + ex
            elif px is not None:
                self._expire_at[key] = time.monotonic() + px / 1000
            else:
                self._expire_at.pop(key, None)
            return True

    async def get(self, key: str) -> str | None:
        async with self._lock:
            if self._is_expired(key):
                return None
            return self._str.get(key)

    async def delete(self, *keys: str) -> int:
        async with self._lock:
            removed = 0
            for key in keys:
                if self._exists(key):
                    removed += 1
                self._drop(key)
            return removed

    async def expire(self, key: str, ttl: int) -> bool:
        async with self._lock:
            if not self._exists(key):
                return False
            self._expire_at[key] = time.monotonic() + ttl
            return True

    # ------------------------------------------------------------------- set
    async def sadd(self, key: str, *members: Any) -> int:
        async with self._lock:
            self._is_expired(key)
            bucket = self._set.setdefault(key, set())
            before = len(bucket)
            bucket.update(str(m) for m in members)
            return len(bucket) - before

    async def scard(self, key: str) -> int:
        async with self._lock:
            if self._is_expired(key):
                return 0
            return len(self._set.get(key, set()))

    async def smembers(self, key: str) -> set[str]:
        async with self._lock:
            if self._is_expired(key):
                return set()
            return set(self._set.get(key, set()))

    async def sismember(self, key: str, member: Any) -> bool:
        async with self._lock:
            if self._is_expired(key):
                return False
            return str(member) in self._set.get(key, set())

    # ------------------------------------------------------------------ hash
    async def hset(
        self,
        key: str,
        field: str | None = None,
        value: Any = None,
        mapping: dict | None = None,
    ) -> int:
        async with self._lock:
            self._is_expired(key)
            bucket = self._hash.setdefault(key, {})
            added = 0
            if field is not None:
                if field not in bucket:
                    added += 1
                bucket[field] = str(value)
            if mapping:
                for k, v in mapping.items():
                    if k not in bucket:
                        added += 1
                    bucket[str(k)] = str(v)
            return added

    async def hgetall(self, key: str) -> dict[str, str]:
        async with self._lock:
            if self._is_expired(key):
                return {}
            return dict(self._hash.get(key, {}))

    # ------------------------------------------------------------------ list
    async def rpush(self, key: str, *values: Any) -> int:
        async with self._lock:
            self._is_expired(key)
            bucket = self._list.setdefault(key, [])
            bucket.extend(str(v) for v in values)
            return len(bucket)

    async def lrange(self, key: str, start: int, end: int) -> list[str]:
        async with self._lock:
            if self._is_expired(key):
                return []
            bucket = self._list.get(key, [])
            # Redis: end включителен, -1 = последний элемент
            if end == -1:
                return bucket[start:]
            return bucket[start:end + 1]


# Синглтон — создаётся один раз при импорте, совместим со старым `redis`
redis: InMemoryRedis = InMemoryRedis()


async def ping() -> bool:
    """Проверка соединения при старте (всегда True — память доступна всегда)."""
    return await redis.ping()


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

async def set_value(key: str, value: Any, ex: int | None = None) -> None:
    """Сохранить значение. ex — TTL в секундах."""
    data = json.dumps(value) if not isinstance(value, str) else value
    await redis.set(key, data, ex=ex)


async def get_value(key: str) -> Any | None:
    """Получить значение. Пробует десериализовать JSON, иначе возвращает строку."""
    raw = await redis.get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw


async def delete_value(key: str) -> None:
    await redis.delete(key)


# ---------------------------------------------------------------------------
# Set helpers (для группового режима — множество user_id ответивших)
# ---------------------------------------------------------------------------

async def sadd_member(key: str, member: Any, ex: int | None = None) -> None:
    """Добавить элемент в SET. Опционально обновить TTL."""
    await redis.sadd(key, str(member))
    if ex is not None:
        await redis.expire(key, ex)


async def scard(key: str) -> int:
    """Количество элементов в SET."""
    return await redis.scard(key)


async def smembers(key: str) -> set[str]:
    """Все элементы SET."""
    return await redis.smembers(key)


async def sismember(key: str, member: Any) -> bool:
    """Проверить наличие элемента в SET."""
    return await redis.sismember(key, str(member))


# ---------------------------------------------------------------------------
# Key builders — централизованные имена ключей
# ---------------------------------------------------------------------------

class RedisKeys:
    """
    Единое место для всех шаблонов ключей.
    Использование: RedisKeys.session_state(session_id)
    """

    @staticmethod
    def session_state(session_id: int) -> str:
        """FSM-состояние активной сессии."""
        return f"session:{session_id}:state"

    @staticmethod
    def session_poll(session_id: int) -> str:
        """Telegram poll_id текущего вопроса сессии."""
        return f"session:{session_id}:poll_id"

    @staticmethod
    def question_answered(session_id: int, question_id: int) -> str:
        """SET user_id-ов ответивших на вопрос (групповой режим)."""
        return f"session:{session_id}:q:{question_id}:answered"

    @staticmethod
    def user_throttle(user_id: int) -> str:
        """Ключ rate-limit для пользователя."""
        return f"throttle:{user_id}"

    @staticmethod
    def quiz_lock(quiz_id: int) -> str:
        """Лок — защита от одновременного запуска двух сессий одного квиза."""
        return f"quiz:{quiz_id}:lock"


# ---------------------------------------------------------------------------
# Quiz lock — защита от одновременного запуска двух сессий одного квиза
# ---------------------------------------------------------------------------

QUIZ_LOCK_TTL = 10  # секунд — достаточно чтобы транзакция создания сессии завершилась


async def acquire_quiz_lock(quiz_id: int) -> bool:
    """
    Пытается захватить лок для quiz_id.
    Возвращает True если лок получен, False если квиз уже запускается.
    SET NX + TTL — атомарная операция, безопасна при конкурентных запросах.
    """
    key = RedisKeys.quiz_lock(quiz_id)
    result = await redis.set(key, "1", ex=QUIZ_LOCK_TTL, nx=True)
    return result is not None


async def release_quiz_lock(quiz_id: int) -> None:
    """Освобождает лок после создания сессии."""
    await redis.delete(RedisKeys.quiz_lock(quiz_id))
