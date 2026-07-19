from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings

engine = create_async_engine(
    settings.db_url,
    echo=False,
    connect_args={"timeout": 15},   # ждать до 15с если БД занята
)

# Устанавливаем SQLite-прагмы на каждое новое соединение из пула.
# WAL — самое важное: читатели не блокируют писателей и наоборот.
@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragmas(dbapi_conn, _record):
    try:
        cursor = dbapi_conn._connection.cursor()   # aiosqlite → sqlite3
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-32000")  # 32 MB страничный кэш
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA mmap_size=134217728")  # 128 MB memory-mapped I/O
        cursor.close()
    except Exception:
        pass  # fallback: прагмы не критичны для запуска

AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def create_all_tables() -> None:
    """Создаёт все таблицы в SQLite-файле. Вызывается при старте бота."""
    import db.models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # WAL mode — записывается в файл БД, остаётся после перезапуска
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        await conn.execute(text("PRAGMA synchronous=NORMAL"))
        # Добавляем banned если не существует (для уже существующих БД)
        try:
            await conn.execute(text(
                "ALTER TABLE user_settings ADD COLUMN banned BOOLEAN NOT NULL DEFAULT FALSE"
            ))
        except Exception:
            pass
        # Добавляем back_false к карточкам (для уже существующих БД)
        try:
            await conn.execute(text(
                "ALTER TABLE cards ADD COLUMN back_false TEXT"
            ))
        except Exception:
            pass
        # Планер: привязка сессии/события к пункту плана (для уже существующих БД)
        for _tbl in ("sessions", "study_events"):
            try:
                await conn.execute(text(
                    f"ALTER TABLE {_tbl} ADD COLUMN plan_item_id INTEGER"
                ))
            except Exception:
                pass
