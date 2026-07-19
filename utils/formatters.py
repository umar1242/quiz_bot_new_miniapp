"""
utils/formatters.py
Форматирование текстовых сообщений бота в HTML (ParseMode.HTML).
Все функции возвращают готовую строку для отправки через aiogram.
"""
from db.models import Quiz
from utils.i18n import t


def fmt_time(seconds: int, lang: str = "ru") -> str:
    """42 → '42 сек', 90 → '1 мин 30 сек'."""
    if seconds < 60:
        return t("fmt.sec", lang, n=seconds)
    m, s = divmod(seconds, 60)
    return t("fmt.min_sec", lang, m=m, s=s) if s else t("fmt.min", lang, m=m)


def fmt_quiz_saved(quiz: Quiz, link: str, lang: str = "ru") -> str:
    """Сообщение после успешного сохранения квиза."""
    q_label = t("fmt.shuffled", lang) if quiz.shuffle_q else t("fmt.in_order", lang)
    a_label = t("fmt.shuffled", lang) if quiz.shuffle_a else t("fmt.in_order", lang)
    return t(
        "fmt.quiz_saved", lang,
        title=quiz.title, count=len(quiz.questions),
        timer=fmt_time(quiz.timer_sec, lang), q_label=q_label, a_label=a_label, link=link,
    )


def fmt_quiz_info(quiz: Quiz, link: str, lang: str = "ru") -> str:
    """Краткая информация о квизе (для меню управления)."""
    q_label = t("fmt.shuffled", lang) if quiz.shuffle_q else t("fmt.in_order", lang)
    a_label = t("fmt.shuffled", lang) if quiz.shuffle_a else t("fmt.in_order", lang)
    return t(
        "fmt.quiz_info", lang,
        title=quiz.title, count=len(quiz.questions),
        timer=fmt_time(quiz.timer_sec, lang), q_label=q_label, a_label=a_label, link=link,
    )


def fmt_solo_result(correct: int, wrong: int, skipped: int, total_sec: int, lang: str = "ru") -> str:
    """Итоговая статистика соло-сессии."""
    total = correct + wrong + skipped
    pct = round(correct / total * 100) if total else 0
    medal = "🥇" if pct >= 90 else "🥈" if pct >= 70 else "🥉" if pct >= 50 else "😔"
    return (
        f"{medal} {t('fmt.solo_result_head', lang)}\n\n"
        f"{t('fmt.solo_correct', lang, correct=correct, total=total)}\n"
        f"{t('fmt.solo_wrong', lang, wrong=wrong)}\n"
        f"{t('fmt.solo_skipped', lang, skipped=skipped)}\n"
        f"{t('fmt.solo_pct', lang, pct=pct)}\n"
        f"{t('fmt.solo_time', lang, time=fmt_time(total_sec, lang))}"
    )


def fmt_group_results(rows: list[dict], lang: str = "ru") -> str:
    """
    Итоговая таблица группового квиза.
    rows — список dict с ключами: username, correct, total
    Отсортировано по убыванию correct.
    """
    if not rows:
        return t("fmt.group_nobody", lang)

    lines = [t("fmt.group_results_head", lang)]
    medals = ["🥇", "🥈", "🥉"]

    for i, row in enumerate(rows):
        medal = medals[i] if i < 3 else f"{i+1}."
        name = row["username"] or t("quiz.participant_n", lang, n=i + 1)
        pct = round(row["correct"] / row["total"] * 100) if row["total"] else 0
        lines.append(
            f"{medal} <b>{name}</b> — {row['correct']}/{row['total']} ({pct}%)"
        )

    return "\n".join(lines)


def fmt_parse_preview(count: int, errors: list[str], lang: str = "ru") -> str:
    """Сообщение после парсинга файла — сколько вопросов нашли и какие ошибки."""
    if errors:
        err_text = "\n".join(f"  • {e}" for e in errors[:10])
        suffix = t("fmt.parse_more", lang, n=len(errors) - 10) if len(errors) > 10 else ""
        return t("fmt.parse_errors", lang, count=count, errors=err_text, suffix=suffix)
    return t("fmt.parse_ok", lang, count=count)


def fmt_group_results_detailed(rows: list[dict], question_stats: list[dict], lang: str = "ru") -> str:
    """
    Расширенная итоговая таблица группового квиза:
    — таблица лидеров с местами
    — топ-3 самых сложных вопроса
    """
    if not rows:
        return t("fmt.group_nobody", lang)

    lines = [t("fmt.group_totals_head", lang)]
    medals = ["🥇", "🥈", "🥉"]

    for i, row in enumerate(rows):
        medal = medals[i] if i < 3 else f"{i+1}."
        name = row["username"] or t("quiz.participant_n", lang, n=i + 1)
        pct = round(row["correct"] / row["total"] * 100) if row["total"] else 0
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
        lines.append(
            f"{medal} <b>{name}</b>\n"
            f"    {row['correct']}/{row['total']} · {pct}% {bar}"
        )

    if question_stats:
        hardest = sorted(question_stats, key=lambda x: x["pct"])[:3]
        lines.append(t("fmt.hardest", lang))
        for q in hardest:
            short = q["question_text"][:60] + "…" if len(q["question_text"]) > 60 else q["question_text"]
            lines.append(t("fmt.hardest_line", lang, num=q["num"], short=short, pct=q["pct"]))

    return "\n".join(lines)


def fmt_solo_result_detailed(
    correct: int, wrong: int, skipped: int, total_sec: int,
    question_stats: list[dict] | None = None, lang: str = "ru",
) -> str:
    """Итоговая статистика соло-сессии с детализацией по вопросам."""
    total = correct + wrong + skipped
    pct = round(correct / total * 100) if total else 0
    medal = "🥇" if pct >= 90 else "🥈" if pct >= 70 else "🥉" if pct >= 50 else "😔"

    lines = [
        f"{medal} {t('fmt.solo_result_head', lang)}\n",
        t("fmt.solo_correct", lang, correct=correct, total=total),
        t("fmt.solo_wrong", lang, wrong=wrong),
        t("fmt.solo_skipped", lang, skipped=skipped),
        t("fmt.solo_pct", lang, pct=pct),
        t("fmt.solo_time", lang, time=fmt_time(total_sec, lang)),
    ]

    if question_stats:
        wrong_list = [q for q in question_stats if not q["is_correct"] and q["answer_text"]][:5]
        if wrong_list:
            lines.append(t("fmt.solo_errors", lang))
            for q in wrong_list:
                short = q["question_text"][:55] + "…" if len(q["question_text"]) > 55 else q["question_text"]
                lines.append(f"  {q['num']}. {short}")
                lines.append(t("fmt.solo_your_answer", lang, answer=q["answer_text"][:50]))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Группировка и пагинация для /myquiz
# ---------------------------------------------------------------------------

PAGE_SIZE = 8  # квизов/групп на странице


def _get_base_title(title: str) -> str:
    """
    Извлекает базовое название квиза без суффикса '_часть_N'.
    'тесты_Умархон_часть_3' → 'тесты_Умархон'
    'обычный_квиз'          → 'обычный_квиз'
    """
    import re
    m = re.match(r'^(.+?)_часть_\d+$', title)
    return m.group(1) if m else title


def group_quizzes(quizzes: list) -> list[dict]:
    """
    Группирует квизы по базовому названию.
    Возвращает список dict:
      {
        "base":    str,          # базовое название группы
        "quizzes": list[Quiz],   # все квизы в группе (по порядку номера части)
        "is_group": bool,        # True если частей > 1
      }
    Порядок групп — по дате создания первого квиза в группе (новые сверху).
    """
    import re
    from collections import OrderedDict

    groups: OrderedDict[str, list] = OrderedDict()
    for q in quizzes:
        base = _get_base_title(q.title)
        groups.setdefault(base, []).append(q)

    result = []
    for base, qs in groups.items():
        # Сортируем части внутри группы по номеру части (или по id)
        def sort_key(q):
            m = re.search(r'_часть_(\d+)$', q.title)
            return int(m.group(1)) if m else q.id
        qs_sorted = sorted(qs, key=sort_key)
        result.append({
            "base": base,
            "quizzes": qs_sorted,
            "is_group": len(qs_sorted) > 1,
        })

    return result


def fmt_quiz_list_grouped(
    groups: list[dict],
    respondents: dict[int, int],
    page: int = 0,
    lang: str = "ru",
) -> str:
    """
    Форматирует страницу списка квизов с группировкой.
    groups  — результат group_quizzes()
    page    — номер страницы (0-based)
    """
    if not groups:
        return t("fmt.no_quizzes", lang)

    total_pages = (len(groups) + PAGE_SIZE - 1) // PAGE_SIZE
    page_groups = groups[page * PAGE_SIZE: (page + 1) * PAGE_SIZE]

    lines = [t("fmt.list_header", lang, page=page + 1, total=total_pages)]

    for g in page_groups:
        if g["is_group"]:
            # Группа частей — показываем одной строкой
            total_q   = sum(len(q.questions) for q in g["quizzes"])
            total_res = sum(respondents.get(q.id, 0) for q in g["quizzes"])
            timer_sec = g["quizzes"][0].timer_sec
            resp_label = t("fmt.respondents", lang, count=total_res) if total_res > 0 else ""
            parts_str = "  ".join(
                f"/quiz_{q.id} {t('fmt.part', lang, n=i + 1)}"
                for i, q in enumerate(g["quizzes"])
            )
            lines.append(
                f"📦 <b>{g['base']}</b>{resp_label}\n"
                + t("fmt.group_line", lang, parts_count=len(g["quizzes"]),
                    total_q=total_q, timer=fmt_time(timer_sec, lang)) + "\n"
                + "   " + parts_str
            )
        else:
            # Одиночный квиз
            q = g["quizzes"][0]
            count = respondents.get(q.id, 0)
            resp_label = t("fmt.respondents", lang, count=count) if count > 0 else ""
            shuffle_a = t("fmt.all", lang) if q.shuffle_a else t("fmt.in_order", lang)
            lines.append(
                f"📋 <b>{q.title}</b>{resp_label}\n"
                + t("fmt.single_line", lang, count=len(q.questions),
                    timer=fmt_time(q.timer_sec, lang), shuffle_a=shuffle_a) + "\n"
                + f"/quiz_{q.id}"
            )

    return "\n\n".join(lines)
