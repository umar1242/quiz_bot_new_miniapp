"""
services/user_service.py
Хранение и чтение языка интерфейса пользователя.

Язык лежит в таблице user_settings (SQLite). Поверх БД — небольшой
in-memory кэш {user_id: lang}, чтобы не дёргать БД на каждый апдейт.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import UserSettings
from utils.i18n import DEFAULT_LANG, normalize_lang

_lang_cache: dict[int, str | None] = {}
_ban_cache:  dict[int, bool] = {}


async def get_lang_raw(db: AsyncSession, user_id: int) -> str | None:
    """Возвращает сохранённый язык пользователя или None, если он его ещё не выбирал."""
    if user_id in _lang_cache:
        return _lang_cache[user_id]

    row = await db.get(UserSettings, user_id)
    lang = row.lang if row else None
    _lang_cache[user_id] = lang
    return lang


async def get_lang(db: AsyncSession, user_id: int) -> str:
    """Язык пользователя или дефолтный, если ещё не выбран."""
    return normalize_lang(await get_lang_raw(db, user_id))


async def set_lang(db: AsyncSession, user_id: int, lang: str) -> None:
    """Сохраняет (или обновляет) язык пользователя."""
    lang = normalize_lang(lang)
    row = await db.get(UserSettings, user_id)
    if row is None:
        db.add(UserSettings(user_id=user_id, lang=lang))
    else:
        row.lang = lang
    await db.flush()
    _lang_cache[user_id] = lang


async def is_banned(db: AsyncSession, user_id: int) -> bool:
    if user_id in _ban_cache:
        return _ban_cache[user_id]
    row = await db.get(UserSettings, user_id)
    banned = bool(row.banned) if row else False
    _ban_cache[user_id] = banned
    return banned


async def set_banned(db: AsyncSession, user_id: int, banned: bool) -> None:
    row = await db.get(UserSettings, user_id)
    if row is None:
        db.add(UserSettings(user_id=user_id, lang=DEFAULT_LANG, banned=banned))
    else:
        row.banned = banned
    await db.flush()
    _ban_cache[user_id] = banned


async def active_user_ids(db: AsyncSession) -> list[int]:
    result = await db.execute(
        select(UserSettings.user_id).where(UserSettings.banned == False)  # noqa: E712
    )
    return list(result.scalars().all())
