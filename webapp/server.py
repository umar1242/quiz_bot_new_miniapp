"""
webapp/server.py
Встроенный aiohttp-сервер Mini App: отдаёт SPA (webapp/static/index.html)
и JSON API. Живёт в том же event loop, что и polling бота.

Наружу торчит только через cloudflared-туннель (HTTPS), сам сервер слушает localhost.
"""
import json
import logging
from pathlib import Path

from aiohttp import web

from config import settings
from db.base import AsyncSessionFactory
from services import planner_service as ps
from webapp.auth import validate_init_data

logger = logging.getLogger(__name__)

_STATIC = Path(__file__).parent / "static"


# ---------------------------------------------------------------------------
# Авторизация запроса
# ---------------------------------------------------------------------------

def _user_id(request: web.Request) -> int | None:
    """user_id из проверенного initData (заголовок X-Init-Data) или dev-обход."""
    init_data = request.headers.get("X-Init-Data", "")
    user = validate_init_data(init_data, settings.BOT_TOKEN)
    if user:
        return int(user["id"])
    if settings.WEBAPP_DEV_USER_ID:
        return int(settings.WEBAPP_DEV_USER_ID)
    return None


def _require_user(handler):
    async def wrapper(request: web.Request):
        uid = _user_id(request)
        if uid is None:
            return web.json_response({"error": "unauthorized"}, status=401)
        request["user_id"] = uid
        return await handler(request)
    return wrapper


async def _body(request: web.Request) -> dict:
    try:
        data = await request.json()
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, Exception):
        return {}


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

async def index(request: web.Request) -> web.Response:
    return web.FileResponse(_STATIC / "index.html")


@_require_user
async def api_dashboard(request: web.Request) -> web.Response:
    async with AsyncSessionFactory() as db:
        data = await ps.get_dashboard(db, request["user_id"])
    data["bot_username"] = settings.BOT_USERNAME
    return web.json_response(data)


@_require_user
async def api_materials(request: web.Request) -> web.Response:
    async with AsyncSessionFactory() as db:
        data = await ps.get_materials(db, request["user_id"])
    return web.json_response(data)


@_require_user
async def api_plan_get(request: web.Request) -> web.Response:
    async with AsyncSessionFactory() as db:
        data = await ps.get_plan(db, request["user_id"])
    data["bot_username"] = settings.BOT_USERNAME
    return web.json_response(data)


@_require_user
async def api_plan_save(request: web.Request) -> web.Response:
    data = await _body(request)
    uid = request["user_id"]
    try:
        async with AsyncSessionFactory() as db:
            async with db.begin():
                plan_id = await ps.create_plan(db, uid, data)
    except ValueError as e:
        return web.json_response({"error": str(e)}, status=400)
    return web.json_response({"ok": True, "id": plan_id})


@_require_user
async def api_plan_add_items(request: web.Request) -> web.Response:
    data = await _body(request)
    uid = request["user_id"]
    try:
        async with AsyncSessionFactory() as db:
            async with db.begin():
                added = await ps.add_plan_items(db, uid, data.get("items") or [])
    except ValueError as e:
        return web.json_response({"error": str(e)}, status=400)
    return web.json_response({"ok": True, "added": added})


@_require_user
async def api_plan_delete(request: web.Request) -> web.Response:
    data = await _body(request)
    async with AsyncSessionFactory() as db:
        async with db.begin():
            ok = await ps.delete_plan(db, request["user_id"], int(data.get("id", 0)))
    return web.json_response({"ok": ok})


# ---------------------------------------------------------------------------
# Сборка и запуск
# ---------------------------------------------------------------------------

from webapp import cert_api, cert_attempt_api, bio_api
from quiz_creator.api.server import generate_md_handler

_STATIC = Path(__file__).parent / "static"
_BIO_APP = _STATIC / "bio-app"
_CERT_APP = _STATIC / "cert-app"
_CREATOR_APP = _STATIC / "creator-app"


async def cert_index(request: web.Request) -> web.Response:
    index_file = _CERT_APP / "index.html"
    if index_file.exists():
        return web.FileResponse(index_file)
    return web.Response(text="Cert app static not found", status=404)


async def bio_index(request: web.Request) -> web.Response:
    index_file = _BIO_APP / "index.html"
    if index_file.exists():
        return web.FileResponse(index_file)
    return web.Response(text="Bio app static not found", status=404)


async def creator_index(request: web.Request) -> web.Response:
    index_file = _CREATOR_APP / "index.html"
    if index_file.exists():
        return web.FileResponse(index_file)
    return web.Response(text="Creator app static not found", status=404)


def create_app(bot=None) -> web.Application:
    app = web.Application()
    app["bot"] = bot

    # Registrations for Cert and Bio APIs
    cert_api.register_routes(app)
    cert_attempt_api.register_routes(app)
    bio_api.register_routes(app)

    app.router.add_get("/", index)
    app.router.add_get("/cert", cert_index)
    app.router.add_get("/bio", bio_index)
    app.router.add_get("/creator", creator_index)
    app.router.add_post("/api/generate-md", generate_md_handler)
    app.router.add_get("/api/dashboard", api_dashboard)
    app.router.add_get("/api/materials", api_materials)
    app.router.add_get("/api/plan", api_plan_get)
    app.router.add_post("/api/plan", api_plan_save)
    app.router.add_post("/api/plan/items", api_plan_add_items)
    app.router.add_post("/api/plan/delete", api_plan_delete)

    app.router.add_static("/cert-app/", _CERT_APP, name="cert-app")
    app.router.add_static("/bio-assets/", _BIO_APP / "assets", name="bio-assets")
    app.router.add_static("/creator/assets/", _CREATOR_APP / "assets", name="creator-assets")
    app.router.add_static("/static/", _STATIC)
    return app


async def start_webapp(bot=None) -> web.AppRunner | None:
    """Поднимает сервер в текущем loop. Возвращает runner для cleanup (или None)."""
    if not settings.WEBAPP_ENABLED:
        logger.info("Mini App отключён (WEBAPP_ENABLED=false)")
        return None
    runner = web.AppRunner(create_app(bot))
    await runner.setup()
    site = web.TCPSite(runner, settings.WEBAPP_HOST, settings.WEBAPP_PORT)
    await site.start()
    logger.info(
        "Mini App слушает http://%s:%s  (public: %s)",
        settings.WEBAPP_HOST, settings.WEBAPP_PORT, settings.WEBAPP_URL or "—",
    )
    return runner
