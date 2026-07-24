"""
webapp/cert_attempt_api.py
API прохождения сертификационного теста: старт попытки, ответы части 1
(мгновенная проверка) и части 2 (баллы по пунктам + фото решения), финиш.
"""
import logging
import uuid
from pathlib import Path

from aiohttp import web

from db.base import AsyncSessionFactory
from services import cert_attempt_service as attempt_service
from services.cert_service import get_variant as get_variant_full
from webapp.cert_api import _body, _require_user

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(__file__).parent / "static" / "uploads" / "cert-solutions"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
_ALLOWED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


@_require_user
async def start_attempt(request: web.Request) -> web.Response:
    data = await _body(request)
    variant_id = int(data.get("variant_id", 0))
    async with AsyncSessionFactory() as db:
        async with db.begin():
            attempt = await attempt_service.start_attempt(db, request["user_id"], variant_id)
            attempt_id = attempt.id
    return web.json_response({"ok": True, "attempt_id": attempt_id})


@_require_user
async def get_attempt(request: web.Request) -> web.Response:
    attempt_id = int(request.match_info["attempt_id"])
    async with AsyncSessionFactory() as db:
        async with db.begin():
            attempt = await attempt_service.get_attempt(db, request["user_id"], attempt_id)
            # Вариант мог быть создан другим пользователем (учителем) — берём его owner_id
            # из уже загруженной связи attempt.variant, а не из текущего ученика.
            variant = await get_variant_full(db, attempt.variant.owner_id, attempt.variant_id)
            result = attempt_service.serialize_attempt_for_student(attempt, variant)
    return web.json_response(result)


@_require_user
async def submit_answer(request: web.Request) -> web.Response:
    attempt_id = int(request.match_info["attempt_id"])
    data = await _body(request)
    question_id = int(data.get("question_id", 0))
    async with AsyncSessionFactory() as db:
        async with db.begin():
            reveal = await attempt_service.submit_part1_answer(db, request["user_id"], attempt_id, question_id, data)
    return web.json_response({"ok": True, **reveal})


@_require_user
async def submit_part2_answer(request: web.Request) -> web.Response:
    attempt_id = int(request.match_info["attempt_id"])
    data = await _body(request)
    question_id = int(data.get("question_id", 0))
    async with AsyncSessionFactory() as db:
        async with db.begin():
            res = await attempt_service.submit_part2_answer(db, request["user_id"], attempt_id, question_id, data)
    return web.json_response({"ok": True, **res})


@_require_user
async def upload_solution_image(request: web.Request) -> web.Response:
    attempt_id = int(request.match_info["attempt_id"])
    reader = await request.multipart()
    field = await reader.next()
    if field is None or field.name != "file":
        return web.json_response({"error": "Файл не передан"}, status=400)
    ext = Path(field.filename or "").suffix.lower()
    if ext not in _ALLOWED_IMAGE_EXT:
        return web.json_response({"error": "Разрешены только изображения"}, status=400)

    adir = UPLOAD_DIR / str(attempt_id)
    adir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest = adir / safe_name

    size = 0
    with open(dest, "wb") as f:
        while True:
            chunk = await field.read_chunk()
            if not chunk:
                break
            size += len(chunk)
            if size > 15 * 1024 * 1024:
                f.close()
                dest.unlink(missing_ok=True)
                return web.json_response({"error": "Файл слишком большой (макс. 15 МБ)"}, status=400)
            f.write(chunk)

    url = f"/static/uploads/cert-solutions/{attempt_id}/{safe_name}"
    return web.json_response({"ok": True, "url": url})


@_require_user
async def finish_part1(request: web.Request) -> web.Response:
    attempt_id = int(request.match_info["attempt_id"])
    async with AsyncSessionFactory() as db:
        async with db.begin():
            await attempt_service.finish_part1_now(db, request["user_id"], attempt_id)
    return web.json_response({"ok": True})


@_require_user
async def finish_attempt(request: web.Request) -> web.Response:
    attempt_id = int(request.match_info["attempt_id"])
    async with AsyncSessionFactory() as db:
        async with db.begin():
            attempt = await attempt_service.finish_now(db, request["user_id"], attempt_id)
            result = attempt_service.serialize_results(attempt)
            variant_title = attempt.variant.title if attempt.variant else "Сертификационный тест"
            user_id = attempt.user_id

    from webapp import runtime
    bot = runtime.get_bot()
    if bot is not None:
        try:
            await bot.send_message(user_id, attempt_service.format_results_text(result, variant_title))
        except Exception:
            logger.exception("Не удалось отправить результаты попытки %s в чат", attempt_id)

    return web.json_response(result)


@_require_user
async def get_results(request: web.Request) -> web.Response:
    attempt_id = int(request.match_info["attempt_id"])
    async with AsyncSessionFactory() as db:
        async with db.begin():
            attempt = await attempt_service.get_attempt(db, request["user_id"], attempt_id)
            result = attempt_service.serialize_results(attempt)
    return web.json_response(result)


def register_routes(app: web.Application) -> None:
    app.router.add_post("/api/cert/attempts", start_attempt)
    app.router.add_get("/api/cert/attempts/{attempt_id}", get_attempt)
    app.router.add_post("/api/cert/attempts/{attempt_id}/answer", submit_answer)
    app.router.add_post("/api/cert/attempts/{attempt_id}/part2-answer", submit_part2_answer)
    app.router.add_post("/api/cert/attempts/{attempt_id}/solution-image", upload_solution_image)
    app.router.add_post("/api/cert/attempts/{attempt_id}/finish-part1", finish_part1)
    app.router.add_post("/api/cert/attempts/{attempt_id}/finish", finish_attempt)
    app.router.add_get("/api/cert/attempts/{attempt_id}/results", get_results)
