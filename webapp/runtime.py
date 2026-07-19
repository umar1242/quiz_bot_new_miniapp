"""
webapp/runtime.py
Живое состояние Mini App, которое может меняться в рантайме (URL туннеля).
Отделено от settings, чтобы роутеры/бот читали актуальный URL даже если он
получен уже после старта (serveo выдаёт его через пару секунд после подключения).
"""
from config import settings

_state = {"url": ""}


def set_webapp_url(url: str) -> None:
    _state["url"] = url or ""


def get_webapp_url() -> str:
    """Актуальный публичный URL: рантайм-туннель важнее статического из .env."""
    return _state["url"] or settings.WEBAPP_URL or ""
