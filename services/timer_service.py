"""
services/timer_service.py
Управление таймерами вопросов через asyncio.
Когда таймер истекает — вызывает колбэк next_question_callback(session_id).
"""
import asyncio
import json
import logging

from redis_client import RedisKeys, redis

logger = logging.getLogger(__name__)

# Словарь активных задач: session_id → asyncio.Task
# Нужен чтобы можно было отменить таймер (например если все ответили раньше в соло)
_tasks: dict[int, asyncio.Task] = {}

# Замок на сессию. Гарантирует, что переход к следующему вопросу выполняет
# только ОДИН обработчик за раз (таймер ИЛИ ответ игрока), а не оба сразу —
# иначе сессия отправляет два вопроса за один шаг.
_locks: dict[int, asyncio.Lock] = {}


def get_session_lock(session_id: int) -> asyncio.Lock:
    """Возвращает (создавая при необходимости) asyncio-замок для сессии."""
    lock = _locks.get(session_id)
    if lock is None:
        lock = asyncio.Lock()
        _locks[session_id] = lock
    return lock


async def start_question_timer(
    session_id: int,
    question_id: int,
    timer_sec: int,
    next_question_callback,   # async callable(session_id: int, bot)
    bot,
) -> None:
    """
    Запускает таймер для вопроса.
    Если уже есть активный таймер для этой сессии — отменяет его.
    """
    cancel_timer(session_id)  # отменяем предыдущий если есть

    if timer_sec == 0:
        return  # практика — без таймера

    task = asyncio.create_task(
        _timer_task(session_id, question_id, timer_sec, next_question_callback, bot)
    )
    _tasks[session_id] = task


async def _timer_task(
    session_id: int,
    question_id: int,
    timer_sec: int,
    next_question_callback,
    bot,
) -> None:
    """Внутренняя задача — ждёт timer_sec и вызывает колбэк."""
    try:
        await asyncio.sleep(timer_sec)
        # Таймер сработал и начинает переход к следующему вопросу. Снимаем себя
        # из реестра ДО колбэка, чтобы параллельный cancel_timer() (из ответа
        # игрока или из start_question_timer следующего вопроса) не отменил уже
        # идущий переход на полпути — иначе вопрос будет пропущен.
        if _tasks.get(session_id) is asyncio.current_task():
            _tasks.pop(session_id, None)
        logger.info("Таймер истёк: session=%s question=%s", session_id, question_id)
        await next_question_callback(session_id, bot)
    except asyncio.CancelledError:
        logger.debug("Таймер отменён: session=%s", session_id)
    except Exception as e:
        logger.exception("Ошибка в timer_task session=%s: %s", session_id, e)
    finally:
        # Снимаем себя только если в реестре всё ещё мы — не затираем таймер
        # следующего вопроса, который мог зарегистрировать колбэк.
        if _tasks.get(session_id) is asyncio.current_task():
            _tasks.pop(session_id, None)


def cancel_timer(session_id: int) -> None:
    """Отменяет активный таймер сессии (если есть)."""
    task = _tasks.pop(session_id, None)
    if task and not task.done():
        task.cancel()


def is_timer_running(session_id: int) -> bool:
    task = _tasks.get(session_id)
    return task is not None and not task.done()


# ---------------------------------------------------------------------------
# Redis: маппинг poll_id → session_id (нужен в poll_answer хэндлере)
# ---------------------------------------------------------------------------

async def save_poll_session(
    poll_id: str,
    session_id: int,
    question_id: int,
    answer_ids: list[int] | None = None,
    ttl: int = 3600,
) -> None:
    """Сохраняет связь poll_id → (session_id, question_id) в Redis."""
    mapping = {
        "session_id": session_id,
        "question_id": question_id,
    }
    if answer_ids is not None:
        mapping["answer_ids"] = json.dumps(answer_ids)
    await redis.hset(f"poll:{poll_id}", mapping=mapping)
    await redis.expire(f"poll:{poll_id}", ttl)


async def get_poll_session(poll_id: str) -> tuple[int, int, list[int] | None] | None:
    """
    Возвращает (session_id, question_id) по poll_id.
    Возвращает None если не найдено.
    """
    data = await redis.hgetall(f"poll:{poll_id}")
    if not data:
        return None
    answer_ids = None
    if data.get("answer_ids"):
        answer_ids = [int(i) for i in json.loads(data["answer_ids"])]
    return int(data["session_id"]), int(data["question_id"]), answer_ids


async def delete_poll_session(poll_id: str) -> None:
    await redis.delete(f"poll:{poll_id}")


# ---------------------------------------------------------------------------
# Redis: порядок вопросов сессии
# ---------------------------------------------------------------------------

async def save_question_order(session_id: int, question_ids: list[int], ttl: int = 86400) -> None:
    """Сохраняет список question_id для сессии в Redis."""
    key = f"session:{session_id}:order"
    await redis.delete(key)
    if question_ids:
        await redis.rpush(key, *[str(i) for i in question_ids])
    await redis.expire(key, ttl)


async def get_question_order(session_id: int) -> list[int]:
    """Читает порядок вопросов из Redis."""
    key = f"session:{session_id}:order"
    items = await redis.lrange(key, 0, -1)
    return [int(i) for i in items]
