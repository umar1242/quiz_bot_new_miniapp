"""
services/export_service.py
Генерация файлов с результатами квиза для скачивания.
Поддерживает форматы: .txt (читаемый) и .csv (для Excel).
"""
import csv
import io
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Quiz
from services.stats_service import get_group_stats, get_group_question_stats, get_solo_stats, get_question_stats


async def export_group_txt(db: AsyncSession, session_id: int, quiz: Quiz) -> bytes:
    """Текстовый отчёт по групповому квизу."""
    rows = await get_group_stats(db, session_id)
    q_stats = await get_group_question_stats(db, session_id)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        f"Квиз: {quiz.title}",
        f"Дата: {now}",
        f"Вопросов: {len(quiz.questions)}",
        "=" * 50,
        "",
        "ТАБЛИЦА РЕЗУЛЬТАТОВ",
        "-" * 50,
    ]

    for i, row in enumerate(rows, start=1):
        name = row["username"] or f"Участник {i}"
        pct = round(row["correct"] / row["total"] * 100) if row["total"] else 0
        lines.append(f"{i:2}. {name:<20} {row['correct']}/{row['total']}  ({pct}%)")

    lines += ["", "СТАТИСТИКА ПО ВОПРОСАМ", "-" * 50]
    for q in q_stats:
        short = q["question_text"][:60] + "…" if len(q["question_text"]) > 60 else q["question_text"]
        lines.append(f"  {q['num']:3}. {short}")
        lines.append(f"       Правильно: {q['correct_count']}/{q['total_count']} ({q['pct']}%)")

    return "\n".join(lines).encode("utf-8")


async def export_group_csv(db: AsyncSession, session_id: int, quiz: Quiz) -> bytes:
    """CSV-отчёт по групповому квизу (открывается в Excel)."""
    rows = await get_group_stats(db, session_id)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Место", "Участник", "Правильных", "Всего", "Процент"])

    for i, row in enumerate(rows, start=1):
        name = row["username"] or f"Участник {i}"
        pct = round(row["correct"] / row["total"] * 100) if row["total"] else 0
        writer.writerow([i, name, row["correct"], row["total"], f"{pct}%"])

    return buf.getvalue().encode("utf-8-sig")  # utf-8-sig = BOM, Excel корректно открывает


async def export_solo_txt(db: AsyncSession, session_id: int, user_id: int, quiz: Quiz) -> bytes:
    """Текстовый отчёт по соло-прохождению."""
    stats = await get_solo_stats(db, session_id, user_id)
    q_stats = await get_question_stats(db, session_id, user_id)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total = stats["correct"] + stats["wrong"] + stats["skipped"]
    pct = round(stats["correct"] / total * 100) if total else 0

    lines = [
        f"Квиз: {quiz.title}",
        f"Дата: {now}",
        f"Результат: {stats['correct']}/{total} ({pct}%)",
        "=" * 50,
        "",
        "ДЕТАЛИЗАЦИЯ ПО ВОПРОСАМ",
        "-" * 50,
    ]

    for q in q_stats:
        status = "✓" if q["is_correct"] else "✗"
        short = q["question_text"][:70] + "…" if len(q["question_text"]) > 70 else q["question_text"]
        lines.append(f"  {status} {q['num']:3}. {short}")
        if not q["is_correct"] and q.get("answer_text"):
            lines.append(f"       Ваш ответ: {q['answer_text'][:60]}")

    return "\n".join(lines).encode("utf-8")
