from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # игнорируем устаревшие PG/Redis переменные в .env
    )

    # Telegram
    BOT_TOKEN: str

    # SQLite — файл в корне проекта (без сервера, идеально для Android/PRoot)
    DB_FILE: str = "quiz_bot.db"

    # Bot settings
    BOT_USERNAME: str = "quiz_bot1242bot"   # без @, нужен для deep link генерации
    DEFAULT_TIMER_SEC: int = 30              # дефолтный таймер вопроса

    # Глобальные админы: telegram user_id через запятую, напр. "12345,67890"
    ADMIN_IDS: str = ""

    # --- Mini App (веб-планер + дашборд) ---
    WEBAPP_ENABLED: bool = True          # поднимать ли встроенный веб-сервер
    WEBAPP_HOST: str = "127.0.0.1"       # localhost — наружу торчит только cloudflared
    WEBAPP_PORT: int = 8080
    WEBAPP_URL: str = ""                 # публичный HTTPS-URL от cloudflared (кнопка Mini App)
    WEBAPP_DEV_USER_ID: int = 0          # >0 — обход проверки initData для локального теста в браузере
    TZ_OFFSET_HOURS: int = 5             # часовой пояс пользователя для группировки по дням (UTC+5)

    # --- Встроенный SSH-туннель (serveo) ---
    # Бот сам поднимает `ssh -R ... serveo.net`, узнаёт публичный URL и ставит кнопку меню.
    # Нужно, когда cloudflared блокируется сетью (DPI). Требует ssh-клиент в системе.
    TUNNEL_ENABLED: bool = False
    TUNNEL_SUBDOMAIN: str = ""            # зарезерв. поддомен serveo (нужен зарегистр. ключ); пусто → случайный URL
    SERVEO_KEY: str = "/root/.ssh/serveo_ed25519"  # приватный ключ для фикс. поддомена (если есть)

    @property
    def db_url(self) -> str:
        """Async DSN для SQLAlchemy + aiosqlite."""
        return f"sqlite+aiosqlite:///{self.DB_FILE}"

    @property
    def admin_ids(self) -> set[int]:
        return {
            int(part)
            for part in self.ADMIN_IDS.replace(" ", "").split(",")
            if part.strip().lstrip("-").isdigit()
        }


# Синглтон — импортировать отовсюду
settings = Settings()
