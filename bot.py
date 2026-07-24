"""
bot.py — точка входа.
Запуск: python bot.py
"""
import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeAllGroupChats

from config import settings
from middlewares import setup_middlewares
from redis_client import ping

_PID_FILE = "/tmp/quiz_bot_new.pid"


def _check_pid_lock() -> None:
    """Выходит если уже запущен другой экземпляр."""
    if os.path.exists(_PID_FILE):
        try:
            old_pid = int(open(_PID_FILE).read().strip())
            os.kill(old_pid, 0)
            # Проверяем что это именно наш процесс (защита от PID reuse после ребута)
            cmdline_path = f"/proc/{old_pid}/cmdline"
            if os.path.exists(cmdline_path):
                cmdline = open(cmdline_path, "rb").read().replace(b"\x00", b" ").decode(errors="replace")
                if "bot.py" in cmdline or "quiz_bot_new" in cmdline:
                    print(f"Уже запущен (PID {old_pid}). Выход.", file=sys.stderr)
                    sys.exit(1)
        except (ProcessLookupError, ValueError):
            pass  # процесс мёртв — удаляем старый PID-файл
    open(_PID_FILE, "w").write(str(os.getpid()))


def _remove_pid_lock() -> None:
    try:
        os.remove(_PID_FILE)
    except FileNotFoundError:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def set_bot_commands(bot: Bot) -> None:
    """Устанавливает команды меню бота."""
    # Личный чат
    private_commands = [
        BotCommand(command="start",      description="🏠 Главное меню / мои квизы"),
        BotCommand(command="myquiz",     description="📚 Список моих квизов"),
        BotCommand(command="flashcards", description="📇 Флешкарты / колоды"),
        BotCommand(command="create_quiz",description="📝 Создать тест (Mini App)"),
        BotCommand(command="settings",   description="⚙️ Настройки / til"),
        BotCommand(command="stop",       description="🛑 Остановить квиз"),
        BotCommand(command="help",       description="❓ Помощь"),
        BotCommand(command="admin",      description="🛠 Админ-панель"),
    ]
    if settings.WEBAPP_URL:
        private_commands.insert(3, BotCommand(command="planner", description="📊 Планер и статистика"))
    await bot.set_my_commands(private_commands, scope=BotCommandScopeDefault())

    # Группы — только /start нужен (запуск квиза по ссылке)
    group_commands = [
        BotCommand(command="start", description="🚀 Запустить квиз (используй ссылку)"),
        BotCommand(command="stop",  description="🛑 Остановить квиз (только создатель)"),
    ]
    await bot.set_my_commands(group_commands, scope=BotCommandScopeAllGroupChats())


async def main() -> None:
    # In-memory хранилище — Redis больше не используется
    if not await ping():
        logger.error("In-memory хранилище недоступно — неожиданная ошибка")
        return

    # Создаём таблицы SQLite при старте (вместо alembic/initdb)
    from db.base import create_all_tables
    await create_all_tables()

    storage = MemoryStorage()

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=storage)

    setup_middlewares(dp)

    # Роутеры — порядок важен: edit и creator должны быть до общих хэндлеров
    from routers.admin      import router as admin_router
    from routers.start      import router as start_router
    from routers.planner    import router as planner_router
    from routers.deck       import router as deck_router
    from routers.creator    import router as creator_router
    from routers.edit       import router as edit_router
    from routers.quiz_solo  import router as solo_router
    from routers.quiz_group import router as group_router
    from routers.inline     import router as inline_router
    from routers.export     import router as export_router
    from routers.cert       import router as cert_router
    from routers.bio_solver import router as bio_solver_router
    from routers.atf_calculator import router as atf_calculator_router

    dp.include_router(admin_router)
    dp.include_router(start_router)
    dp.include_router(planner_router)
    dp.include_router(cert_router)
    dp.include_router(bio_solver_router)
    dp.include_router(atf_calculator_router)
    # deck_router — ДО creator: его file-хэндлер (в состоянии CreateDeck) должен
    # перехватывать документ раньше, чем общий F.document в creator.py
    dp.include_router(deck_router)
    dp.include_router(creator_router)
    dp.include_router(edit_router)
    dp.include_router(solo_router)
    dp.include_router(group_router)
    dp.include_router(inline_router)
    dp.include_router(export_router)


    # Mini App: встроенный веб-сервер + кнопка меню Telegram
    from webapp.server import start_webapp
    from webapp import runtime
    webapp_runner = await start_webapp(bot)

    async def _set_menu_button(url: str) -> None:
        from aiogram.types import MenuButtonWebApp, WebAppInfo
        runtime.set_webapp_url(url)
        try:
            await bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(text="📊 Планер", web_app=WebAppInfo(url=url))
            )
            logger.info("Кнопка меню Mini App обновлена: %s", url)
        except Exception as e:
            logger.warning("Не удалось установить кнопку меню Mini App: %s", e)

    # Статический URL из .env (если задан) — ставим сразу
    if settings.WEBAPP_URL:
        await _set_menu_button(settings.WEBAPP_URL)

    # Либо поднимаем встроенный SSH-туннель (serveo), URL придёт асинхронно
    if settings.TUNNEL_ENABLED:
        from webapp.tunnel import run_tunnel
        asyncio.create_task(run_tunnel(_set_menu_button))

    # Устанавливаем команды меню при старте
    await set_bot_commands(bot)

    # Восстановление после рестарта — завершаем зависшие сессии
    from services.startup_service import recover_on_startup
    await recover_on_startup(bot)

    # poll_answer явно добавляем — resolve_used_update_types иногда пропускает его
    # если хэндлер зарегистрирован внутри sub-router а не dp напрямую
    allowed = list(set(dp.resolve_used_update_types()) | {"poll_answer", "inline_query"})

    logger.info("Бот запущен ✅")
    try:
        await dp.start_polling(bot, allowed_updates=allowed)
    finally:
        if webapp_runner is not None:
            await webapp_runner.cleanup()


if __name__ == "__main__":
    _check_pid_lock()
    try:
        asyncio.run(main())
    finally:
        _remove_pid_lock()
