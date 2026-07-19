"""Alembic env.py — настроен для asyncpg + SQLAlchemy async."""
import asyncio
import sys
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy import pool

# Добавляем /app в sys.path чтобы найти модули db, config и т.д.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импортируем Base и все модели (чтобы autogenerate видел таблицы)
from db.base import Base
import db.models  # noqa: F401 — side-effect import, регистрирует модели в Base.metadata

config = context.config
fileConfig(config.config_file_name)  # логирование из alembic.ini

target_metadata = Base.metadata


def get_url() -> str:
    from config import settings
    return settings.db_url


def run_migrations_offline() -> None:
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    cfg = config.get_section(config.config_ini_section)
    cfg["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        cfg,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())