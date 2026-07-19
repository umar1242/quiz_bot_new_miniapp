"""
services/planner_service.py
Логика Mini App «Учебный план».

Модель:
 - Пользователь создаёт ПЛАН на период (start_day..end_day) и добавляет задания
   (квиз или колода), для каждого — целевое число прохождений за период («интервал»).
 - Прохождение засчитывается ТОЛЬКО когда задание запущено «с регистрацией» из
   планера И доведено до конца (пишется StudyEvent с plan_item_id). Обычный запуск
   из бота и остановка на середине НЕ регистрируются.
 - Дашборд агрегирует прогресс: пройдено/цель в %, правильно/неправильно.

StudyEvent.created_at пишется в UTC; день считаем в локальном поясе пользователя
(config.TZ_OFFSET_HOURS), чтобы корректно попадать в границы периода.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.base import AsyncSessionFactory
from db.models import (
    Card,
    Deck,
    Plan,
    PlanItem,
    Question,
    Quiz,
    StudyEvent,
    StudyKind,
)

_OFFSET = timedelta(hours=settings.TZ_OFFSET_HOURS)

# Тип задания плана -> какой StudyKind засчитывается как прохождение.
_ITEM_STUDY_KIND = {"quiz": StudyKind.quiz, "tf": StudyKind.tf}


# ---------------------------------------------------------------------------
# Дата/время
# ---------------------------------------------------------------------------

def _local_day(dt: datetime) -> str:
    """UTC-datetime -> 'YYYY-MM-DD' в локальном часовом поясе пользователя."""
    return (dt + _OFFSET).strftime("%Y-%m-%d")


def today_str() -> str:
    return _local_day(datetime.utcnow())


# ---------------------------------------------------------------------------
# Материалы пользователя (для выбора при создании плана)
# ---------------------------------------------------------------------------

async def get_materials(db: AsyncSession, user_id: int) -> dict:
    """Колоды и квизы пользователя с количеством карточек/вопросов."""
    decks_res = await db.execute(
        select(Deck.id, Deck.title, func.count(Card.id))
        .outerjoin(Card, Card.deck_id == Deck.id)
        .where(Deck.owner_id == user_id)
        .group_by(Deck.id, Deck.title)
        .order_by(Deck.created_at.desc())
    )
    quizzes_res = await db.execute(
        select(Quiz.id, Quiz.title, func.count(Question.id))
        .outerjoin(Question, Question.quiz_id == Quiz.id)
        .where(Quiz.owner_id == user_id)
        .group_by(Quiz.id, Quiz.title)
        .order_by(Quiz.created_at.desc())
    )
    return {
        "decks":   [{"id": r[0], "title": r[1], "count": int(r[2])} for r in decks_res.all()],
        "quizzes": [{"id": r[0], "title": r[1], "count": int(r[2])} for r in quizzes_res.all()],
    }


# ---------------------------------------------------------------------------
# План: создание / получение / удаление
# ---------------------------------------------------------------------------

async def _get_active_plan(db: AsyncSession, user_id: int) -> Plan | None:
    res = await db.execute(
        select(Plan)
        .where(Plan.user_id == user_id, Plan.active == True)  # noqa: E712
        .order_by(Plan.id.desc())
    )
    return res.scalars().first()


async def create_plan(db: AsyncSession, user_id: int, data: dict) -> int:
    """
    Создаёт новый план из {start_day, end_day, items:[{kind, ref_id, title, target}]}.
    Прежний активный план деактивируется — активным остаётся только новый.
    """
    start = str(data.get("start_day", "")).strip()[:10]
    end = str(data.get("end_day", "")).strip()[:10]
    if not start or not end:
        raise ValueError("Не заданы даты периода")
    if end < start:
        start, end = end, start

    raw_items = data.get("items") or []
    clean: list[dict] = []
    for it in raw_items:
        kind = str(it.get("kind", ""))
        if kind not in _ITEM_STUDY_KIND:
            continue
        try:
            ref_id = int(it.get("ref_id") or 0)
        except (TypeError, ValueError):
            continue
        if ref_id <= 0:
            continue
        clean.append({
            "kind": kind,
            "ref_id": ref_id,
            "title": str(it.get("title", "")).strip()[:255] or "Задание",
            "target": max(1, min(999, int(it.get("target", 1) or 1))),
        })
    if not clean:
        raise ValueError("Не выбрано ни одного задания")

    await db.execute(
        update(Plan)
        .where(Plan.user_id == user_id, Plan.active == True)  # noqa: E712
        .values(active=False)
    )

    plan = Plan(
        user_id=user_id,
        title=(str(data.get("title", "")).strip()[:255] or f"{start} — {end}"),
        start_day=start,
        end_day=end,
        active=True,
    )
    db.add(plan)
    await db.flush()

    for it in clean:
        db.add(PlanItem(
            plan_id=plan.id, user_id=user_id,
            kind=it["kind"], ref_id=it["ref_id"],
            title=it["title"], target=it["target"],
        ))
    await db.flush()
    return plan.id


async def add_plan_items(db: AsyncSession, user_id: int, items: list[dict]) -> int:
    """
    Дозаписывает задания в АКТИВНЫЙ план пользователя, не создавая новый и не трогая
    существующие пункты и прогресс. Дубликаты (тот же kind+ref_id уже в плане)
    пропускаются. Возвращает число реально добавленных пунктов.
    """
    plan = await _get_active_plan(db, user_id)
    if plan is None:
        raise ValueError("Нет активного плана — сначала создай план")

    existing = {(i.kind, i.ref_id) for i in await _plan_items(db, plan.id)}
    added = 0
    for it in (items or []):
        kind = str(it.get("kind", ""))
        if kind not in _ITEM_STUDY_KIND:
            continue
        try:
            ref_id = int(it.get("ref_id") or 0)
        except (TypeError, ValueError):
            continue
        if ref_id <= 0 or (kind, ref_id) in existing:
            continue
        db.add(PlanItem(
            plan_id=plan.id, user_id=user_id,
            kind=kind, ref_id=ref_id,
            title=str(it.get("title", "")).strip()[:255] or "Задание",
            target=max(1, min(999, int(it.get("target", 1) or 1))),
        ))
        existing.add((kind, ref_id))
        added += 1

    if added == 0:
        raise ValueError("Нечего добавить — задания уже в плане")
    await db.flush()
    return added


async def delete_plan(db: AsyncSession, user_id: int, plan_id: int) -> bool:
    plan = await db.get(Plan, plan_id)
    if plan is None or plan.user_id != user_id:
        return False
    # Удаляем связанные события ДО удаления пунктов: иначе они осиротеют, а SQLite
    # переиспользует id пунктов при создании нового плана — и старые прохождения
    # «воскреснут» в новом плане.
    item_ids = [i.id for i in await _plan_items(db, plan.id)]
    if item_ids:
        await db.execute(
            sa_delete(StudyEvent).where(StudyEvent.plan_item_id.in_(item_ids))
        )
    await db.delete(plan)   # каскадом удалит пункты плана
    return True


async def get_plan_item(db: AsyncSession, user_id: int, item_id: int) -> PlanItem | None:
    """Пункт плана с проверкой владельца — для сценария регистрации в боте."""
    item = await db.get(PlanItem, item_id)
    if item is None or item.user_id != user_id:
        return None
    return item


async def _plan_items(db: AsyncSession, plan_id: int) -> list[PlanItem]:
    res = await db.execute(
        select(PlanItem).where(PlanItem.plan_id == plan_id).order_by(PlanItem.id)
    )
    return list(res.scalars().all())


async def get_plan(db: AsyncSession, user_id: int) -> dict:
    """Активный план с заданиями (для вкладки «План» и кнопок запуска ▶)."""
    plan = await _get_active_plan(db, user_id)
    if plan is None:
        return {"plan": None}
    items = await _plan_items(db, plan.id)
    return {
        "plan": {
            "id": plan.id,
            "title": plan.title,
            "start_day": plan.start_day,
            "end_day": plan.end_day,
            "items": [
                {"id": i.id, "kind": i.kind, "ref_id": i.ref_id,
                 "title": i.title, "target": i.target}
                for i in items
            ],
        }
    }


# ---------------------------------------------------------------------------
# Регистрация выполненного прохождения
# ---------------------------------------------------------------------------

async def log_registered_event(
    db: AsyncSession, user_id: int, plan_item_id: int,
    kind: StudyKind, ref_id: int | None, correct: int, total: int,
) -> None:
    """Пишет событие в уже открытой транзакции (для квизов — есть готовый db)."""
    db.add(StudyEvent(
        user_id=user_id, kind=kind, ref_id=ref_id, plan_item_id=plan_item_id,
        correct=int(correct or 0), total=int(total or 0),
    ))


async def log_registered_event_standalone(
    user_id: int, plan_item_id: int,
    kind: StudyKind, ref_id: int | None, correct: int, total: int,
) -> None:
    """Открывает собственную сессию — для мест без готового db (тест В/Н)."""
    try:
        async with AsyncSessionFactory() as db:
            async with db.begin():
                await log_registered_event(
                    db, user_id, plan_item_id, kind, ref_id, correct, total
                )
    except Exception:
        # Логирование статистики не должно ломать основной сценарий бота.
        pass


# ---------------------------------------------------------------------------
# Дашборд: прогресс по активному плану
# ---------------------------------------------------------------------------

async def get_dashboard(db: AsyncSession, user_id: int) -> dict:
    """
    Прогресс по активному плану:
      - overall: пройдено/цель в % (пройдено ограничено целью по каждому пункту),
        суммарно правильно/неправильно и точность;
      - items: по каждому заданию — пройдено/цель в %, правильно/неправильно в %.
    """
    today = today_str()
    plan = await _get_active_plan(db, user_id)
    if plan is None:
        return {"today": today, "plan": None}

    items = await _plan_items(db, plan.id)
    item_ids = [i.id for i in items]

    agg: dict[int, dict] = {i.id: {"done": 0, "correct": 0, "total": 0} for i in items}
    if item_ids:
        ev_res = await db.execute(
            select(StudyEvent.plan_item_id, StudyEvent.correct,
                   StudyEvent.total, StudyEvent.created_at)
            .where(StudyEvent.plan_item_id.in_(item_ids))
        )
        for pid, correct, total, created_at in ev_res.all():
            a = agg.get(pid)
            if a is None or created_at is None:
                continue
            # Защита от переиспользованных SQLite id пунктов: считаем только
            # прохождения, зарегистрированные ПОСЛЕ создания плана. Сравниваем
            # datetime в Python (в SQL строковое сравнение форматов ненадёжно).
            if plan.created_at is not None and created_at < plan.created_at:
                continue
            day = _local_day(created_at)
            if day < plan.start_day or day > plan.end_day:
                continue  # прохождение вне границ периода не считаем
            a["done"] += 1
            a["correct"] += int(correct or 0)
            a["total"] += int(total or 0)

    items_out = []
    tot_done = tot_target = tot_correct = tot_answered = 0
    for i in items:
        a = agg[i.id]
        capped = min(a["done"], i.target)
        pct = (capped / i.target) if i.target else 0.0
        accuracy = (a["correct"] / a["total"]) if a["total"] else 0.0
        items_out.append({
            "id": i.id,
            "kind": i.kind,
            "ref_id": i.ref_id,
            "title": i.title,
            "target": i.target,
            "done": a["done"],
            "pct": round(pct, 4),
            "correct": a["correct"],
            "incorrect": a["total"] - a["correct"],
            "answered": a["total"],
            "accuracy": round(accuracy, 4),
        })
        tot_done += capped
        tot_target += i.target
        tot_correct += a["correct"]
        tot_answered += a["total"]

    overall_pct = (tot_done / tot_target) if tot_target else 0.0
    overall_acc = (tot_correct / tot_answered) if tot_answered else 0.0

    # Сколько дней осталось до конца периода (включительно), либо статус.
    try:
        end_dt = datetime.strptime(plan.end_day, "%Y-%m-%d")
        today_dt = datetime.strptime(today, "%Y-%m-%d")
        days_left = (end_dt - today_dt).days
    except ValueError:
        days_left = None

    return {
        "today": today,
        "plan": {
            "id": plan.id,
            "title": plan.title,
            "start_day": plan.start_day,
            "end_day": plan.end_day,
            "days_left": days_left,
        },
        "overall": {
            "done": tot_done,
            "target": tot_target,
            "pct": round(overall_pct, 4),
            "correct": tot_correct,
            "incorrect": tot_answered - tot_correct,
            "answered": tot_answered,
            "accuracy": round(overall_acc, 4),
        },
        "items": items_out,
    }
