"""
webapp/planner_api.py
API для планнера (Mini App) — учебный план на период.
Адаптировано из quiz_bot_new для cert_bot_miniapp.
"""
import logging

from aiohttp import web

from config import settings
from db.base import AsyncSessionFactory
from services import planner_service as ps
from webapp.auth import validate_init_data
from webapp.cert_api import _body, _require_user

logger = logging.getLogger(__name__)


@_require_user
async def get_materials(request: web.Request) -> web.Response:
    async with AsyncSessionFactory() as db:
        data = await ps.get_materials(db, request["user_id"])
    return web.json_response(data)


@_require_user
async def get_plan(request: web.Request) -> web.Response:
    async with AsyncSessionFactory() as db:
        data = await ps.get_plan(db, request["user_id"])
    bot_username = getattr(settings, "BOT_USERNAME", "") or ""
    return web.json_response({**data, "bot_username": bot_username})


@_require_user
async def create_plan(request: web.Request) -> web.Response:
    body = await _body(request)
    async with AsyncSessionFactory() as db:
        async with db.begin():
            plan_id = await ps.create_plan(db, request["user_id"], body)
    return web.json_response({"ok": True, "plan_id": plan_id})


@_require_user
async def add_plan_items(request: web.Request) -> web.Response:
    body = await _body(request)
    items = body.get("items", [])
    async with AsyncSessionFactory() as db:
        async with db.begin():
            added = await ps.add_plan_items(db, request["user_id"], items)
    return web.json_response({"ok": True, "added": added})


@_require_user
async def delete_plan(request: web.Request) -> web.Response:
    body = await _body(request)
    plan_id = int(body.get("id", 0))
    async with AsyncSessionFactory() as db:
        async with db.begin():
            ok = await ps.delete_plan(db, request["user_id"], plan_id)
    return web.json_response({"ok": ok})


@_require_user
async def get_dashboard(request: web.Request) -> web.Response:
    async with AsyncSessionFactory() as db:
        data = await ps.get_dashboard(db, request["user_id"])
    bot_username = getattr(settings, "BOT_USERNAME", "") or ""
    return web.json_response({**data, "bot_username": bot_username})


def register_routes(app: web.Application) -> None:
    app.router.add_get("/api/materials", get_materials)
    app.router.add_get("/api/plan", get_plan)
    app.router.add_post("/api/plan", create_plan)
    app.router.add_post("/api/plan/items", add_plan_items)
    app.router.add_post("/api/plan/delete", delete_plan)
    app.router.add_get("/api/dashboard", get_dashboard)
