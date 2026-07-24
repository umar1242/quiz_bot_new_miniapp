"""
services/cert_service.py
CRUD для конструктора сертификационных тестов (Mini App).
"""
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import (
    CertBand,
    CertMatchPair,
    CertOpenAnswer,
    CertOption,
    CertQType,
    CertQuestion,
    CertQuestionImage,
    CertVariant,
    CertVariantStatus,
)
from dto.cert_dto import CertQuestionDraftDTO

# Границы номеров по типу задания (см. спецификацию нацсертификата по биологии)
Y1_RANGE = (1, 32)
Y2_RANGE = (33, 35)
O1_RANGE = (36, 40)
O2_RANGE = (41, 43)
O2_MAX_POINTS = {41: 30, 42: 35, 43: 10}


def _full_opts():
    return (
        selectinload(CertVariant.questions).selectinload(CertQuestion.options),
        selectinload(CertVariant.questions).selectinload(CertQuestion.match_pairs),
        selectinload(CertVariant.questions).selectinload(CertQuestion.open_answers),
        selectinload(CertVariant.questions).selectinload(CertQuestion.bands),
        selectinload(CertVariant.questions).selectinload(CertQuestion.images),
    )


async def list_variants(db: AsyncSession, owner_id: int) -> list[CertVariant]:
    q = await db.execute(
        select(CertVariant)
        .where(CertVariant.owner_id == owner_id)
        .order_by(CertVariant.created_at.desc())
    )
    return list(q.scalars().all())


async def get_variant(db: AsyncSession, owner_id: int, variant_id: int) -> CertVariant | None:
    q = await db.execute(
        select(CertVariant)
        .where(CertVariant.id == variant_id, CertVariant.owner_id == owner_id)
        .options(*_full_opts())
    )
    return q.scalar_one_or_none()


async def create_variant(db: AsyncSession, owner_id: int, title: str) -> CertVariant:
    variant = CertVariant(owner_id=owner_id, title=title or "Вариант")
    db.add(variant)
    await db.flush()
    return variant


async def delete_variant(db: AsyncSession, owner_id: int, variant_id: int) -> bool:
    variant = await get_variant(db, owner_id, variant_id)
    if not variant:
        return False
    await db.delete(variant)
    return True


async def _next_number(db: AsyncSession, variant_id: int, lo: int, hi: int) -> int | None:
    """Следующий свободный номер в диапазоне [lo, hi], либо None если диапазон заполнен."""
    q = await db.execute(
        select(sa_func.max(CertQuestion.number)).where(
            CertQuestion.variant_id == variant_id,
            CertQuestion.number >= lo,
            CertQuestion.number <= hi,
        )
    )
    current_max = q.scalar_one_or_none()
    nxt = lo if current_max is None else current_max + 1
    return nxt if nxt <= hi else None


async def import_y1_drafts(
    db: AsyncSession, owner_id: int, variant_id: int, drafts: list[CertQuestionDraftDTO],
    on_created=None,
) -> list[CertQuestion]:
    """
    Добавляет распарсенные задания Y1 в вариант, начиная с номера 1.
    Парсер — источник истины для раздела Y1: перед вставкой новых заданий
    все прежние задания Y1 в этом варианте удаляются, независимо от того,
    были они добавлены вручную или предыдущим импортом. Остальные разделы
    (Y2/O1/O2) не затрагиваются.

    `on_created(question, draft)` — необязательный асинхронный колбэк,
    вызывается сразу после создания каждого задания (например, чтобы
    сохранить на диск и прикрепить картинки, извлечённые парсером
    markdown — см. dto.cert_dto.CertQuestionDraftDTO.images).
    """
    variant = await get_variant(db, owner_id, variant_id)
    if not variant:
        raise ValueError("Вариант не найден")

    for old in [q for q in variant.questions if q.qtype == CertQType.Y1]:
        await db.delete(old)
    await db.flush()

    created: list[CertQuestion] = []
    for draft in drafts:
        number = await _next_number(db, variant_id, *Y1_RANGE)
        if number is None:
            raise ValueError(
                f"Раздел Y1 переполнен (максимум {Y1_RANGE[1]} заданий) — "
                f"добавлено {len(created)} из {len(drafts)}"
            )
        question = CertQuestion(
            variant_id=variant_id, number=number, part=1, qtype=CertQType.Y1,
            text=draft.text, points=1, needs_image=draft.needs_image,
        )
        db.add(question)
        await db.flush()
        for i, opt in enumerate(draft.options):
            db.add(CertOption(question_id=question.id, position=i, text=opt.text, is_correct=opt.is_correct))
        await db.flush()
        if on_created is not None:
            await on_created(question, draft)
        created.append(question)

    return created


async def add_manual_question(db: AsyncSession, owner_id: int, variant_id: int, payload: dict) -> CertQuestion:
    """
    Добавляет задание, созданное вручную в интерфейсе mini app.
    Поддерживаются все типы, включая Y1 — но учтите: если позже сделать
    импорт Y1 через парсер, все вручную добавленные задания Y1 будут
    удалены и заменены распарсенными (см. import_y1_drafts).
    """
    variant = await get_variant(db, owner_id, variant_id)
    if not variant:
        raise ValueError("Вариант не найден")

    qtype = payload.get("qtype")
    ranges = {"Y1": Y1_RANGE, "Y2": Y2_RANGE, "O1": O1_RANGE, "O2": O2_RANGE}
    if qtype not in ranges:
        raise ValueError("Неизвестный тип задания")

    lo, hi = ranges[qtype]
    number = await _next_number(db, variant_id, lo, hi)
    if number is None:
        raise ValueError(f"Раздел {qtype} переполнен")

    part = 2 if qtype == "O2" else 1
    default_points = O2_MAX_POINTS.get(number, 1) if qtype == "O2" else 1

    question = CertQuestion(
        variant_id=variant_id, number=number, part=part, qtype=CertQType(qtype),
        text=payload.get("text", ""), points=payload.get("points", default_points),
    )
    db.add(question)
    await db.flush()

    if qtype == "Y1":
        for i, opt in enumerate(payload.get("options", [])):
            db.add(CertOption(
                question_id=question.id, position=i,
                text=opt.get("text", ""), is_correct=opt.get("is_correct", False),
            ))
    elif qtype == "Y2":
        for i, pair in enumerate(payload.get("pairs", [])):
            db.add(CertMatchPair(
                question_id=question.id, position=i,
                left_text=pair.get("left", ""), right_text=pair.get("right", "A"),
            ))
        for i, opt in enumerate(payload.get("options", [])):
            db.add(CertOption(
                question_id=question.id, position=i,
                text=opt.get("text", ""), is_correct=False,
            ))
    elif qtype == "O1":
        for ans in payload.get("answers", []):
            db.add(CertOpenAnswer(
                question_id=question.id, text=ans.get("text", ""),
                match_mode=ans.get("match_mode", "exact"), tolerance=ans.get("tolerance"),
            ))
    elif qtype == "O2":
        for i, band in enumerate(payload.get("bands", []), start=1):
            db.add(CertBand(
                question_id=question.id, band_no=band.get("band_no", i),
                prompt=band.get("prompt"), reference_answer=band.get("reference_answer", ""),
                match_mode=band.get("match_mode", "numeric"), tolerance=band.get("tolerance"),
                max_points=band.get("max_points", 1),
            ))

    return question


async def update_question(db: AsyncSession, owner_id: int, question_id: int, payload: dict) -> CertQuestion:
    question = await _get_question_checked(db, owner_id, question_id)

    if "text" in payload:
        question.text = payload["text"]
    if "points" in payload:
        question.points = payload["points"]

    if question.qtype == CertQType.Y1 and "options" in payload:
        for opt in list(question.options):
            await db.delete(opt)
        await db.flush()
        for i, opt in enumerate(payload["options"]):
            db.add(CertOption(question_id=question.id, position=i, text=opt.get("text", ""), is_correct=opt.get("is_correct", False)))

    if question.qtype == CertQType.Y2 and ("pairs" in payload or "options" in payload):
        for p in list(question.match_pairs):
            await db.delete(p)
        for o in list(question.options):
            await db.delete(o)
        await db.flush()
        for i, pair in enumerate(payload.get("pairs", [])):
            db.add(CertMatchPair(question_id=question.id, position=i, left_text=pair.get("left", ""), right_text=pair.get("right", "A")))
        for i, opt in enumerate(payload.get("options", [])):
            db.add(CertOption(question_id=question.id, position=i, text=opt.get("text", ""), is_correct=False))

    if question.qtype == CertQType.O1 and "answers" in payload:
        for a in list(question.open_answers):
            await db.delete(a)
        await db.flush()
        for ans in payload["answers"]:
            db.add(CertOpenAnswer(question_id=question.id, text=ans.get("text", ""), match_mode=ans.get("match_mode", "exact"), tolerance=ans.get("tolerance")))

    if question.qtype == CertQType.O2 and "bands" in payload:
        for b in list(question.bands):
            await db.delete(b)
        await db.flush()
        for i, band in enumerate(payload["bands"], start=1):
            db.add(CertBand(
                question_id=question.id, band_no=band.get("band_no", i), prompt=band.get("prompt"),
                reference_answer=band.get("reference_answer", ""), match_mode=band.get("match_mode", "numeric"),
                tolerance=band.get("tolerance"), max_points=band.get("max_points", 1),
            ))

    return question


async def delete_question(db: AsyncSession, owner_id: int, question_id: int) -> None:
    question = await _get_question_checked(db, owner_id, question_id)
    await db.delete(question)


async def add_image(db: AsyncSession, owner_id: int, question_id: int, file_path: str, caption: str | None) -> CertQuestionImage:
    question = await _get_question_checked(db, owner_id, question_id)
    position = len(question.images)
    image = CertQuestionImage(question_id=question.id, position=position, file_path=file_path, caption=caption)
    db.add(image)
    await db.flush()
    question.needs_image = False
    return image


async def delete_image(db: AsyncSession, owner_id: int, question_id: int, image_id: int) -> None:
    question = await _get_question_checked(db, owner_id, question_id)
    for img in question.images:
        if img.id == image_id:
            await db.delete(img)
            return
    raise ValueError("Изображение не найдено")


async def _get_question_checked(db: AsyncSession, owner_id: int, question_id: int) -> CertQuestion:
    q = await db.execute(
        select(CertQuestion)
        .join(CertVariant, CertQuestion.variant_id == CertVariant.id)
        .where(CertQuestion.id == question_id, CertVariant.owner_id == owner_id)
        .options(
            selectinload(CertQuestion.options),
            selectinload(CertQuestion.match_pairs),
            selectinload(CertQuestion.open_answers),
            selectinload(CertQuestion.bands),
            selectinload(CertQuestion.images),
        )
    )
    question = q.scalar_one_or_none()
    if not question:
        raise ValueError("Задание не найдено")
    return question


async def set_status(db: AsyncSession, owner_id: int, variant_id: int, status: str) -> CertVariant:
    variant = await get_variant(db, owner_id, variant_id)
    if not variant:
        raise ValueError("Вариант не найден")
    variant.status = CertVariantStatus(status)
    return variant


def serialize_variant(variant: CertVariant) -> dict:
    return {
        "id": variant.id,
        "title": variant.title,
        "status": variant.status.value,
        "part1_timer_sec": variant.part1_timer_sec,
        "part2_timer_sec": variant.part2_timer_sec,
        "created_at": variant.created_at.isoformat() if variant.created_at else None,
        "questions": [serialize_question(q) for q in variant.questions],
        "progress": _progress(variant),
    }


def serialize_variant_brief(variant: CertVariant, question_count: int = 0) -> dict:
    return {
        "id": variant.id,
        "title": variant.title,
        "status": variant.status.value,
        "created_at": variant.created_at.isoformat() if variant.created_at else None,
        "question_count": question_count,
    }


def serialize_question(q: CertQuestion) -> dict:
    data = {
        "id": q.id,
        "number": q.number,
        "part": q.part,
        "qtype": q.qtype.value,
        "text": q.text,
        "points": q.points,
        "needs_image": q.needs_image,
        "images": [
            {"id": im.id, "url": f"/static/uploads/cert/{im.file_path}", "caption": im.caption}
            for im in q.images
        ],
    }
    if q.qtype == CertQType.Y1:
        data["options"] = [{"id": o.id, "text": o.text, "is_correct": o.is_correct} for o in q.options]
    elif q.qtype == CertQType.Y2:
        data["pairs"] = [{"id": p.id, "left": p.left_text, "right": p.right_text} for p in q.match_pairs]
        data["options"] = [{"id": o.id, "text": o.text} for o in q.options]
    elif q.qtype == CertQType.O1:
        data["answers"] = [{"id": a.id, "text": a.text, "match_mode": a.match_mode, "tolerance": a.tolerance} for a in q.open_answers]
    elif q.qtype == CertQType.O2:
        data["bands"] = [
            {"id": b.id, "band_no": b.band_no, "prompt": b.prompt, "reference_answer": b.reference_answer,
             "match_mode": b.match_mode, "tolerance": b.tolerance, "max_points": b.max_points}
            for b in q.bands
        ]
    return data


def _progress(variant: CertVariant) -> dict:
    by_type = {"Y1": 0, "Y2": 0, "O1": 0, "O2": 0}
    needs_image = 0
    for q in variant.questions:
        by_type[q.qtype.value] += 1
        if q.needs_image:
            needs_image += 1
    # Y1: 32 заданий, Y2: 1 задание (группа из 3 вопросов), O1: 5 заданий, O2: 3 задания
    total_slots = (Y1_RANGE[1] - Y1_RANGE[0] + 1) + 1 + (O1_RANGE[1] - O1_RANGE[0] + 1) + (O2_RANGE[1] - O2_RANGE[0] + 1)
    filled = sum(by_type.values())
    return {
        "by_type": by_type,
        "filled": filled,
        "total_slots": total_slots,
        "needs_image": needs_image,
        "percent": round(filled / total_slots * 100) if total_slots else 0,
    }
