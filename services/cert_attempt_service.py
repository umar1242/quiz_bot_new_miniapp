"""
services/cert_attempt_service.py
Прохождение сертификационного теста учеником: старт попытки, ответы с
мгновенной автопроверкой (часть 1: Y1/Y2/O1, общий таймер), письменная
часть (часть 2: O2, отдельный таймер, баллы по пунктам + фото решения).
"""
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import (
    CertAttempt,
    CertAttemptStatus,
    CertQType,
    CertQuestion,
    CertResponse,
    CertVariant,
)

PART1_TYPES = (CertQType.Y1, CertQType.Y2, CertQType.O1)


def _now() -> datetime:
    # SQLite не хранит tzinfo — храним и сравниваем наивные UTC datetime.
    return datetime.utcnow()


async def _load_variant(db: AsyncSession, variant_id: int) -> CertVariant:
    q = await db.execute(
        select(CertVariant)
        .where(CertVariant.id == variant_id)
        .options(
            selectinload(CertVariant.questions).selectinload(CertQuestion.options),
            selectinload(CertVariant.questions).selectinload(CertQuestion.match_pairs),
            selectinload(CertVariant.questions).selectinload(CertQuestion.open_answers),
            selectinload(CertVariant.questions).selectinload(CertQuestion.bands),
            selectinload(CertVariant.questions).selectinload(CertQuestion.images),
        )
    )
    variant = q.scalar_one_or_none()
    if not variant:
        raise ValueError("Вариант не найден")
    return variant


async def start_attempt(db: AsyncSession, user_id: int, variant_id: int) -> CertAttempt:
    variant = await _load_variant(db, variant_id)
    max_part1 = sum(q.points for q in variant.questions if q.qtype in PART1_TYPES)
    max_part2 = sum(q.points for q in variant.questions if q.qtype == CertQType.O2)

    attempt = CertAttempt(
        variant_id=variant.id, user_id=user_id, status=CertAttemptStatus.part1,
        part1_started_at=_now(), part1_deadline=_now() + timedelta(seconds=variant.part1_timer_sec),
        max_part1=max_part1, max_part2=max_part2,
    )
    db.add(attempt)
    await db.flush()
    return attempt


async def _load_attempt(db: AsyncSession, user_id: int, attempt_id: int) -> CertAttempt:
    q = await db.execute(
        select(CertAttempt)
        .where(CertAttempt.id == attempt_id, CertAttempt.user_id == user_id)
        .options(selectinload(CertAttempt.responses), selectinload(CertAttempt.variant))
    )
    attempt = q.scalar_one_or_none()
    if not attempt:
        raise ValueError("Попытка не найдена")
    return attempt


async def get_attempt(db: AsyncSession, user_id: int, attempt_id: int) -> CertAttempt:
    attempt = await _load_attempt(db, user_id, attempt_id)
    await _check_expiry(db, attempt)
    return attempt


async def _check_expiry(db: AsyncSession, attempt: CertAttempt) -> None:
    """Ленивый автопереход по истечении таймера части."""
    now = _now()
    if attempt.status == CertAttemptStatus.part1 and now >= attempt.part1_deadline:
        await _begin_part2(db, attempt)
    if attempt.status == CertAttemptStatus.part2 and attempt.part2_deadline and now >= attempt.part2_deadline:
        attempt.status = CertAttemptStatus.finished
        attempt.finished_at = now


async def _begin_part2(db: AsyncSession, attempt: CertAttempt) -> None:
    variant = await _load_variant(db, attempt.variant_id)
    has_o2 = any(q.qtype == CertQType.O2 for q in variant.questions)
    if has_o2:
        attempt.status = CertAttemptStatus.part2
        attempt.part2_started_at = _now()
        attempt.part2_deadline = _now() + timedelta(seconds=variant.part2_timer_sec)
    else:
        attempt.status = CertAttemptStatus.finished
        attempt.finished_at = _now()


async def finish_part1_now(db: AsyncSession, user_id: int, attempt_id: int) -> CertAttempt:
    attempt = await _load_attempt(db, user_id, attempt_id)
    if attempt.status != CertAttemptStatus.part1:
        return attempt
    await _begin_part2(db, attempt)
    return attempt


async def finish_now(db: AsyncSession, user_id: int, attempt_id: int) -> CertAttempt:
    attempt = await _load_attempt(db, user_id, attempt_id)
    if attempt.status != CertAttemptStatus.finished:
        attempt.status = CertAttemptStatus.finished
        attempt.finished_at = _now()
    return attempt


def _num_match(user_val: str, ref_val: str, tolerance: float | None) -> bool:
    try:
        return abs(float(user_val.replace(",", ".")) - float(ref_val.replace(",", "."))) <= (tolerance or 0)
    except (ValueError, AttributeError):
        return user_val.strip() == ref_val.strip()


def _o1_is_correct(text: str, question: CertQuestion) -> bool:
    norm = (text or "").strip().lower()
    for ans in question.open_answers:
        if ans.match_mode == "numeric":
            if _num_match(text or "", ans.text, ans.tolerance):
                return True
        elif norm == ans.text.strip().lower():
            return True
    return False


async def _get_question(db: AsyncSession, question_id: int) -> CertQuestion:
    q = await db.execute(
        select(CertQuestion)
        .where(CertQuestion.id == question_id)
        .options(
            selectinload(CertQuestion.options),
            selectinload(CertQuestion.match_pairs),
            selectinload(CertQuestion.open_answers),
            selectinload(CertQuestion.bands),
        )
    )
    question = q.scalar_one_or_none()
    if not question:
        raise ValueError("Задание не найдено")
    return question


async def _upsert_response(db: AsyncSession, attempt: CertAttempt, question_id: int, answer: dict,
                            is_correct: bool | None, points_earned: float, points_max: float,
                            qtype: CertQType) -> CertResponse:
    existing = next((r for r in attempt.responses if r.question_id == question_id), None)
    if existing:
        if qtype == CertQType.O2:
            attempt.points_part2 -= existing.points_earned
        else:
            attempt.points_part1 -= existing.points_earned
        existing.answer = answer
        existing.is_correct = is_correct
        existing.points_earned = points_earned
        existing.points_max = points_max
        resp = existing
    else:
        resp = CertResponse(
            attempt_id=attempt.id, question_id=question_id, answer=answer,
            is_correct=is_correct, points_earned=points_earned, points_max=points_max,
        )
        db.add(resp)
        attempt.responses.append(resp)
    return resp


async def submit_part1_answer(db: AsyncSession, user_id: int, attempt_id: int, question_id: int, payload: dict) -> dict:
    attempt = await _load_attempt(db, user_id, attempt_id)
    await _check_expiry(db, attempt)
    if attempt.status != CertAttemptStatus.part1:
        raise ValueError("Время тестовой части истекло")

    question = await _get_question(db, question_id)
    if question.qtype not in PART1_TYPES:
        raise ValueError("Задание не относится к тестовой части")

    reveal: dict = {}

    if question.qtype == CertQType.Y1:
        option_id = payload.get("option_id")
        correct = next((o for o in question.options if o.is_correct), None)
        is_correct = option_id is not None and correct is not None and option_id == correct.id
        points = question.points if is_correct else 0
        answer = {"option_id": option_id}
        reveal = {"is_correct": is_correct, "correct_option_id": correct.id if correct else None}

    elif question.qtype == CertQType.Y2:
        choices = payload.get("choices", {})  # {subquestion_pair_id: selected_letter}
        total = len(question.match_pairs) or 1
        correct_count = sum(
            1 for p in question.match_pairs
            if str(choices.get(str(p.id), "")) == p.right_text
        )
        is_correct = correct_count == total
        points = round(question.points * correct_count / total, 2)
        answer = {"choices": choices}
        reveal = {
            "is_correct": is_correct,
            "correct_choices": {str(p.id): p.right_text for p in question.match_pairs},
            "correct_count": correct_count,
            "total": total,
        }

    elif question.qtype == CertQType.O1:
        text = payload.get("text", "")
        is_correct = _o1_is_correct(text, question)
        points = question.points if is_correct else 0
        answer = {"text": text}
        reveal = {
            "is_correct": is_correct,
            "reference_answers": [a.text for a in question.open_answers],
        }

    else:
        raise ValueError("Неизвестный тип задания")

    resp = await _upsert_response(db, attempt, question_id, answer, reveal.get("is_correct"), points, question.points, question.qtype)
    attempt.points_part1 += points
    await db.flush()

    reveal["points_earned"] = resp.points_earned
    reveal["points_max"] = question.points
    return reveal


async def submit_part2_answer(db: AsyncSession, user_id: int, attempt_id: int, question_id: int, payload: dict) -> dict:
    attempt = await _load_attempt(db, user_id, attempt_id)
    await _check_expiry(db, attempt)
    if attempt.status != CertAttemptStatus.part2:
        raise ValueError("Письменная часть недоступна (не начата или уже завершена)")

    question = await _get_question(db, question_id)
    if question.qtype != CertQType.O2:
        raise ValueError("Задание не относится к письменной части")

    band_values: dict = payload.get("bands", {})  # {band_id: str}
    image_url = payload.get("image_url")

    points = 0.0
    max_points = 0.0
    for band in question.bands:
        max_points += band.max_points
        val = band_values.get(str(band.id), "")
        if not val:
            continue
        matched = (
            _num_match(val, band.reference_answer, band.tolerance)
            if band.match_mode == "numeric"
            else val.strip().lower() == band.reference_answer.strip().lower()
        )
        if matched:
            points += band.max_points

    answer = {"bands": band_values, "image_url": image_url}
    resp = await _upsert_response(db, attempt, question_id, answer, None, points, max_points, question.qtype)
    attempt.points_part2 += points
    await db.flush()

    return {
        "points_earned": resp.points_earned,
        "points_max": max_points,
        # ответы части 2 не показываются мгновенно — итог виден после сдачи всего теста
    }


def serialize_attempt_for_student(attempt: CertAttempt, variant: CertVariant) -> dict:
    """Вид теста для ученика: без правильных ответов, с уже сохранёнными ответами (для резюме)."""
    answered = {r.question_id: r for r in attempt.responses}
    now = _now()

    def part1_left() -> int:
        return max(0, int((attempt.part1_deadline - now).total_seconds()))

    def part2_left() -> int:
        if not attempt.part2_deadline:
            return 0
        return max(0, int((attempt.part2_deadline - now).total_seconds()))

    questions = []
    for q in sorted(variant.questions, key=lambda x: x.number):
        item = {
            "id": q.id, "number": q.number, "part": q.part, "qtype": q.qtype.value,
            "text": q.text, "points": q.points,
            "images": [{"id": im.id, "url": f"/static/uploads/cert/{im.file_path}"} for im in q.images],
        }
        r = answered.get(q.id)
        if q.qtype == CertQType.Y1:
            item["options"] = [{"id": o.id, "text": o.text} for o in q.options]
        elif q.qtype == CertQType.Y2:
            item["subquestions"] = [{"id": p.id, "text": p.left_text} for p in q.match_pairs]
            item["options"] = [{"id": o.id, "text": o.text} for o in q.options]
            # Preserve shuffled order of letter labels from options
        elif q.qtype == CertQType.O2:
            item["bands"] = [{"id": b.id, "band_no": b.band_no, "prompt": b.prompt, "max_points": b.max_points} for b in q.bands]
        if r:
            item["answered"] = True
            item["your_answer"] = r.answer
            item["is_correct"] = r.is_correct
            item["points_earned"] = r.points_earned
        questions.append(item)

    return {
        "id": attempt.id,
        "status": attempt.status.value,
        "part1_seconds_left": part1_left(),
        "part2_seconds_left": part2_left() if attempt.status == CertAttemptStatus.part2 else None,
        "questions": questions,
    }


def _bar(percent: int, width: int = 10) -> str:
    filled = round(width * percent / 100)
    return "▓" * filled + "░" * (width - filled)


def format_results_text(results: dict, variant_title: str) -> str:
    p1, p2, tot = results["part1"], results["part2"], results["total"]
    lines = [
        f"🎓 <b>{variant_title}</b> — тест завершён",
        "",
        f"📝 Тестовая часть: {_bar(p1['percent'])}  <b>{p1['percent']}%</b>  ({p1['earned']}/{p1['max']})",
        f"✍️ Письменная часть: {_bar(p2['percent'])}  <b>{p2['percent']}%</b>  ({p2['earned']}/{p2['max']})",
        "",
        f"🏆 Итог: {_bar(tot['percent'])}  <b>{tot['percent']}%</b>  ({tot['earned']}/{tot['max']})",
    ]
    return "\n".join(lines)


def serialize_results(attempt: CertAttempt) -> dict:
    pct1 = round(attempt.points_part1 / attempt.max_part1 * 100) if attempt.max_part1 else 0
    pct2 = round(attempt.points_part2 / attempt.max_part2 * 100) if attempt.max_part2 else 0
    total_earned = attempt.points_part1 + attempt.points_part2
    total_max = attempt.max_part1 + attempt.max_part2
    pct_total = round(total_earned / total_max * 100) if total_max else 0
    return {
        "part1": {"earned": attempt.points_part1, "max": attempt.max_part1, "percent": pct1},
        "part2": {"earned": attempt.points_part2, "max": attempt.max_part2, "percent": pct2},
        "total": {"earned": total_earned, "max": total_max, "percent": pct_total},
        "status": attempt.status.value,
    }
