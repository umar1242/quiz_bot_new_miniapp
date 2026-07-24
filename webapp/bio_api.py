import json
import logging
from aiohttp import web
from config import settings
from webapp.auth import validate_init_data

logger = logging.getLogger(__name__)

def _require_user(request: web.Request) -> dict | None:
    init_data = request.headers.get("X-Init-Data", "")
    if settings.WEBAPP_DEV_USER_ID > 0:
        return {"id": settings.WEBAPP_DEV_USER_ID, "first_name": "Dev"}
    user = validate_init_data(init_data, settings.BOT_TOKEN)
    return user

async def api_save_cross(request: web.Request) -> web.Response:
    user = _require_user(request)
    if user is None:
        return web.json_response({"error": "unauthorized"}, status=401)
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid json"}, status=400)

    from db.base import AsyncSessionFactory
    from db.models import SavedCross

    async with AsyncSessionFactory() as session:
        cross = SavedCross(
            user_id=user["id"],
            title=body.get("title", "Без названия"),
            parent1=body.get("parent1", ""),
            parent2=body.get("parent2", ""),
            phenotypes_json=json.dumps(body.get("phenotypes", []), ensure_ascii=False),
        )
        session.add(cross)
        await session.commit()

    return web.json_response({"ok": True, "id": cross.id})

async def api_my_crosses(request: web.Request) -> web.Response:
    user = _require_user(request)
    if user is None:
        return web.json_response({"error": "unauthorized"}, status=401)

    from db.base import AsyncSessionFactory
    from db.models import SavedCross
    from sqlalchemy import select

    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(SavedCross)
            .where(SavedCross.user_id == user["id"])
            .order_by(SavedCross.created_at.desc())
            .limit(50)
        )
        crosses = result.scalars().all()

    items = []
    for c in crosses:
        items.append({
            "id": c.id,
            "title": c.title,
            "parent1": c.parent1,
            "parent2": c.parent2,
            "phenotypes": json.loads(c.phenotypes_json) if c.phenotypes_json else [],
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })

    return web.json_response({"crosses": items})

async def api_send_result(request: web.Request) -> web.Response:
    user = _require_user(request)
    if user is None:
        return web.json_response({"error": "unauthorized"}, status=401)

    try:
        body = await request.json()
        text = body.get("text", "")
    except Exception:
        return web.json_response({"error": "invalid json"}, status=400)

    from webapp.runtime import get_bot
    bot = get_bot()
    if bot and text:
        try:
            await bot.send_message(chat_id=user["id"], text=text)
            return web.json_response({"ok": True})
        except Exception as e:
            logger.error("Failed to send message: %s", e)
            return web.json_response({"error": str(e)}, status=500)

    return web.json_response({"error": "No bot or text"}, status=400)

def register_routes(app: web.Application):
    app.router.add_post("/api/save-cross", api_save_cross)
    app.router.add_get("/api/my-crosses", api_my_crosses)
    app.router.add_post("/api/send-result", api_send_result)
