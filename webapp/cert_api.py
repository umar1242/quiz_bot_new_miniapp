"""
webapp/cert_api.py
API конструктора сертификационных тестов (Mini App): варианты, задания,
импорт из спец-парсера, загрузка рисунков.
"""
import logging
import re
import uuid
from pathlib import Path

from aiohttp import web

from config import settings
from db.base import AsyncSessionFactory
from services import cert_service as cs
from services.parser.md_parser import parse_cert_md, finalize_question_md, MdParser
from services.parser.cert_txt_parser import questions_to_drafts
from webapp.auth import validate_init_data

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(__file__).parent / "static" / "uploads" / "cert"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

_ALLOWED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
_SAFE_NAME = re.compile(r"[^a-zA-Z0-9_.-]+")

_md_parser = MdParser()


def _user_id(request: web.Request) -> int | None:
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
        try:
            return await handler(request)
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)
    return wrapper


async def _body(request: web.Request) -> dict:
    try:
        data = await request.json()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Варианты
# ---------------------------------------------------------------------------

@_require_user
async def list_variants(request: web.Request) -> web.Response:
    async with AsyncSessionFactory() as db:
        variants = await cs.list_variants(db, request["user_id"])
        out = []
        for v in variants:
            await db.refresh(v, attribute_names=["questions"])
            out.append(cs.serialize_variant_brief(v, len(v.questions)))
    return web.json_response({"variants": out})


@_require_user
async def create_variant(request: web.Request) -> web.Response:
    data = await _body(request)
    async with AsyncSessionFactory() as db:
        async with db.begin():
            variant = await cs.create_variant(db, request["user_id"], data.get("title", ""))
        variant_id = variant.id
    return web.json_response({"ok": True, "id": variant_id})


@_require_user
async def get_variant(request: web.Request) -> web.Response:
    variant_id = int(request.match_info["variant_id"])
    async with AsyncSessionFactory() as db:
        variant = await cs.get_variant(db, request["user_id"], variant_id)
        if not variant:
            return web.json_response({"error": "not_found"}, status=404)
        return web.json_response(cs.serialize_variant(variant))


@_require_user
async def delete_variant(request: web.Request) -> web.Response:
    variant_id = int(request.match_info["variant_id"])
    async with AsyncSessionFactory() as db:
        async with db.begin():
            ok = await cs.delete_variant(db, request["user_id"], variant_id)
    return web.json_response({"ok": ok})


@_require_user
async def set_status(request: web.Request) -> web.Response:
    variant_id = int(request.match_info["variant_id"])
    data = await _body(request)
    async with AsyncSessionFactory() as db:
        async with db.begin():
            await cs.set_status(db, request["user_id"], variant_id, data.get("status", "draft"))
    return web.json_response({"ok": True})


# ---------------------------------------------------------------------------
# Импорт Y1: формат +++ / ..... / @
# ---------------------------------------------------------------------------

async def _save_draft_images(db, user_id: int, question, draft) -> None:
    """
    Сохраняет на диск картинки, уже извлечённые парсером (например, base64
    из markdown), и прикрепляет их к только что созданному заданию —
    так же, как обычная ручная загрузка рисунка через upload_image().
    """
    for raw_bytes, ext in draft.images:
        if not ext.startswith("."):
            ext = f".{ext}"
        if ext not in _ALLOWED_IMAGE_EXT:
            continue

        safe_name = f"{uuid.uuid4().hex}{ext}"
        qdir = UPLOAD_DIR / str(question.id)
        qdir.mkdir(parents=True, exist_ok=True)
        dest = qdir / safe_name
        dest.write_bytes(raw_bytes)

        rel_path = f"{question.id}/{safe_name}"
        try:
            await cs.add_image(db, user_id, question.id, rel_path, None)
        except ValueError:
            dest.unlink(missing_ok=True)


@_require_user
async def import_y1(request: web.Request) -> web.Response:
    """
    Импорт заданий Y1 в формате +++ / ..... / @.

    Принимает:
      - {"text": "..."} JSON — вставленный markdown-текст
      - multipart/form-data с файлом — только .md

    Формат:
        +++
        Текст вопроса (markdown, таблицы | col | col |, картинки)
        .....
        Вариант 1
        .....
        @Вариант 2 (правильный)
        .....
        Вариант 3
        .....
        Вариант 4
        +++

    Импорт полностью заменяет раздел Y1: и вручную добавленные задания,
    и результат предыдущего импорта — парсер всегда побеждает.
    """
    variant_id = int(request.match_info["variant_id"])
    content_type = request.content_type

    if content_type == "multipart/form-data":
        reader = await request.multipart()
        field = await reader.next()
        if field is None or field.name != "file":
            return web.json_response({"error": "Файл не передан"}, status=400)
        filename = field.filename or "upload.md"

        # Проверяем расширение — принимаем только .md
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext != ".md":
            return web.json_response(
                {"error": "Принимаются только .md файлы. Пожалуйста, сохраните файл в формате Markdown (.md)."},
                status=400,
            )

        file_bytes = await field.read(decode=True)
        try:
            raw_text = await _md_parser._to_text(file_bytes)
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)
    else:
        data = await _body(request)
        raw_text = data.get("text", "")
        if not raw_text.strip():
            return web.json_response({"error": "Пустой текст"}, status=400)

    # Парсим формат +++ / ..... / @
    questions, images = parse_cert_md(raw_text)
    drafts = questions_to_drafts(questions, images)

    async with AsyncSessionFactory() as db:
        async with db.begin():
            async def on_created(question, draft):
                # Финализируем markdown: сохраняем base64 картинки на диск, обновляем URL
                if draft.images:
                    finalized, rel_paths = finalize_question_md(
                        question.text, draft.images, UPLOAD_DIR, question.id
                    )
                    if finalized != question.text:
                        question.text = finalized
                    for rel_path in rel_paths:
                        try:
                            await cs.add_image(db, request["user_id"], question.id, rel_path, None)
                        except ValueError:
                            pass

            created = await cs.import_y1_drafts(
                db, request["user_id"], variant_id, drafts,
                on_created=on_created,
            )
        added = len(created)

    return web.json_response({"ok": True, "added": added, "found": len(drafts)})


# ---------------------------------------------------------------------------
# Задания (Y2 / O1 / O2 создаются вручную, Y1 редактируется после импорта)
# ---------------------------------------------------------------------------

@_require_user
async def add_question(request: web.Request) -> web.Response:
    variant_id = int(request.match_info["variant_id"])
    data = await _body(request)
    async with AsyncSessionFactory() as db:
        async with db.begin():
            q = await cs.add_manual_question(db, request["user_id"], variant_id, data)
            await db.flush()
            await db.refresh(q, attribute_names=["options", "match_pairs", "open_answers", "bands", "images"])
            result = cs.serialize_question(q)
    return web.json_response({"ok": True, "question": result})


@_require_user
async def update_question(request: web.Request) -> web.Response:
    question_id = int(request.match_info["question_id"])
    data = await _body(request)
    async with AsyncSessionFactory() as db:
        async with db.begin():
            q = await cs.update_question(db, request["user_id"], question_id, data)
            await db.flush()
            await db.refresh(q, attribute_names=["options", "match_pairs", "open_answers", "bands", "images"])
            result = cs.serialize_question(q)
    return web.json_response({"ok": True, "question": result})


@_require_user
async def delete_question(request: web.Request) -> web.Response:
    question_id = int(request.match_info["question_id"])
    async with AsyncSessionFactory() as db:
        async with db.begin():
            await cs.delete_question(db, request["user_id"], question_id)
    return web.json_response({"ok": True})


# ---------------------------------------------------------------------------
# Рисунки
# ---------------------------------------------------------------------------

@_require_user
async def upload_image(request: web.Request) -> web.Response:
    question_id = int(request.match_info["question_id"])
    reader = await request.multipart()
    field = await reader.next()
    if field is None or field.name != "file":
        return web.json_response({"error": "Файл не передан"}, status=400)

    ext = Path(field.filename or "").suffix.lower()
    if ext not in _ALLOWED_IMAGE_EXT:
        return web.json_response({"error": "Разрешены только изображения (png/jpg/webp/gif)"}, status=400)

    safe_name = f"{uuid.uuid4().hex}{ext}"
    qdir = UPLOAD_DIR / str(question_id)
    qdir.mkdir(parents=True, exist_ok=True)
    dest = qdir / safe_name

    size = 0
    with open(dest, "wb") as f:
        while True:
            chunk = await field.read_chunk()
            if not chunk:
                break
            size += len(chunk)
            if size > 10 * 1024 * 1024:
                f.close()
                dest.unlink(missing_ok=True)
                return web.json_response({"error": "Файл слишком большой (макс. 10 МБ)"}, status=400)
            f.write(chunk)

    rel_path = f"{question_id}/{safe_name}"
    async with AsyncSessionFactory() as db:
        async with db.begin():
            try:
                image = await cs.add_image(db, request["user_id"], question_id, rel_path, None)
            except ValueError as e:
                dest.unlink(missing_ok=True)
                return web.json_response({"error": str(e)}, status=400)
        image_id, image_path = image.id, image.file_path

    return web.json_response({"ok": True, "image": {"id": image_id, "url": f"/static/uploads/cert/{image_path}"}})


@_require_user
async def delete_image(request: web.Request) -> web.Response:
    question_id = int(request.match_info["question_id"])
    image_id = int(request.match_info["image_id"])
    async with AsyncSessionFactory() as db:
        async with db.begin():
            await cs.delete_image(db, request["user_id"], question_id, image_id)
    return web.json_response({"ok": True})


def register_routes(app: web.Application) -> None:
    app.router.add_get("/api/cert/variants", list_variants)
    app.router.add_post("/api/cert/variants", create_variant)
    app.router.add_get("/api/cert/variants/{variant_id}", get_variant)
    app.router.add_delete("/api/cert/variants/{variant_id}", delete_variant)
    app.router.add_post("/api/cert/variants/{variant_id}/status", set_status)
    app.router.add_post("/api/cert/variants/{variant_id}/import-y1", import_y1)
    app.router.add_post("/api/cert/variants/{variant_id}/questions", add_question)
    app.router.add_put("/api/cert/questions/{question_id}", update_question)
    app.router.add_delete("/api/cert/questions/{question_id}", delete_question)
    app.router.add_post("/api/cert/questions/{question_id}/images", upload_image)
    app.router.add_delete("/api/cert/questions/{question_id}/images/{image_id}", delete_image)

