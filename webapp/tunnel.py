"""
webapp/tunnel.py
Встроенный менеджер SSH-туннеля через serveo.net.

Зачем: на сетях с DPI, где cloudflared (и quick, и named) блокируется,
SSH-туннель на порт 22/443 проходит. Бот сам запускает `ssh -R ... serveo.net`,
вычитывает выданный публичный HTTPS-URL и переподнимает соединение при обрыве.

serveo для анонимных/бесплатных подключений показывает браузеру страницу-предупреждение;
она обходится query-параметром `?serveo-skip-browser-warning=true`, который мы
добавляем к URL (302 + долгоживущая cookie → дальше отдаётся само приложение).
"""
import asyncio
import logging
import os
import re

from config import settings

logger = logging.getLogger(__name__)

# URL вида https://<hex>-<ip>.serveousercontent.com или https://<name>.serveo.net
_URL_RE = re.compile(r"https://[A-Za-z0-9.-]+\.serveo(?:usercontent)?\.(?:net|com)")

_SKIP = "/?serveo-skip-browser-warning=true"


def _ssh_command() -> list[str]:
    cmd = [
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ServerAliveInterval=30",
        "-o", "ServerAliveCountMax=3",
        "-o", "ExitOnForwardFailure=yes",
    ]
    if settings.SERVEO_KEY and os.path.exists(settings.SERVEO_KEY):
        cmd += ["-i", settings.SERVEO_KEY]
    name = settings.TUNNEL_SUBDOMAIN.strip()
    remote = f"{name}:80:localhost:{settings.WEBAPP_PORT}" if name else f"80:localhost:{settings.WEBAPP_PORT}"
    cmd += ["-R", remote, "serveo.net"]
    return cmd


async def run_tunnel(on_url) -> None:
    """
    Бесконечно держит SSH-туннель. При каждом получении публичного URL вызывает
    `await on_url(full_url)` (full_url уже с обходом заглушки). Переподключается
    при обрыве. Вызывать как asyncio-таск.
    """
    backoff = 5
    while True:
        cmd = _ssh_command()
        logger.info("Туннель serveo: запускаю %s", " ".join(cmd))
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                stdin=asyncio.subprocess.DEVNULL,
            )
        except FileNotFoundError:
            logger.error("ssh не найден — туннель невозможен. Установи openssh-client.")
            return

        got_url = False
        try:
            assert proc.stdout is not None
            async for raw in proc.stdout:
                line = raw.decode(errors="replace").strip()
                if not line:
                    continue
                # URL берём ТОЛЬКО из строки "Forwarding HTTP traffic from ...".
                # Прочие ссылки serveo (console.serveo.net в подсказках) игнорируем.
                if "forwarding" in line.lower():
                    m = _URL_RE.search(line)
                    if m and "console.serveo.net" not in m.group(0):
                        full = m.group(0) + _SKIP
                        got_url = True
                        backoff = 5
                        logger.info("Туннель поднят, публичный URL: %s", full)
                        try:
                            await on_url(full)
                        except Exception as e:
                            logger.warning("on_url колбэк упал: %s", e)
                elif "register" in line.lower() or "subdomain" in line.lower():
                    logger.info("serveo: %s", line)
        except Exception as e:
            logger.warning("Ошибка чтения вывода туннеля: %s", e)
        finally:
            if proc.returncode is None:
                proc.terminate()
                try:
                    await asyncio.wait_for(proc.wait(), timeout=5)
                except asyncio.TimeoutError:
                    proc.kill()

        wait = backoff if got_url else min(backoff * 2, 120)
        backoff = min(backoff * 2, 120)
        logger.warning("Туннель serveo закрылся — переподключение через %sс", wait)
        await asyncio.sleep(wait)
