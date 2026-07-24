"""
services/parser/md_parser.py
Парсер .md для сертификационных тестов.

Формат файла:
    +++
    Текст вопроса (может содержать markdown-таблицы | col | col |,
    inline-картинки ![alt](url), любую markdown-разметку)
    .....
    Вариант 1
    .....
    @Вариант 2 (правильный — @ в начале)
    .....
    Вариант 3
    .....
    Вариант 4
    +++

Разделители:
    - +++ (строго 3 плюса на отдельной строке) — разделитель между тестами
    - ..... (строго 5 точек на отдельной строке) — разделитель между
      вопросом/вариантами ответа
    - @ в начале строки варианта — маркер правильного ответа

Таблицы GFM (| cell | cell |) внутри текста вопроса — визуальный контент,
отображается react-markdown. Pandoc grid-tables конвертируются автоматически.

Картинки:
    - base64 ![alt](data:image/...) → сохраняются на диск, URL подставляется inline
    - обычные пути/URL ![alt](file.png) → pending:imgN плейсхолдер
"""
import base64
import re
import uuid
from pathlib import Path

from services.parser.base import BaseParser

# ---------- Разделители нового формата ----------
_QUESTION_SEP = re.compile(r'^\+{3}\s*$', re.MULTILINE)  # строго +++
_OPTION_SEP = re.compile(r'^\.{5}\s*$', re.MULTILINE)     # строго .....
_CORRECT_MARK = '@'  # @ перед правильным ответом

# ---------- Картинки ----------
_MD_IMAGE = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
_DATA_URI = re.compile(r'^data:image/(?P<ext>[a-zA-Z0-9+.-]+);base64,(?P<data>.+)$', re.DOTALL)
_EXT_ALIASES = {"jpeg": "jpg"}
_ALLOWED_EXT = {"png", "jpg", "webp", "gif"}

# ---------- Grid table detection (Pandoc-style ASCII tables) ----------
_GRID_BORDER = re.compile(r'^\+[-=:]+(\+[-=:]+)+\+\s*$')
_GRID_DATA = re.compile(r'^\|(.+\|)+\s*$')


class MdParser(BaseParser):
    """Общий .md → текст (используется флешкартами и обычными квизами)."""

    async def _to_text(self, file_bytes: bytes) -> str:
        for encoding in ("utf-8", "cp1251", "latin-1"):
            try:
                return file_bytes.decode(encoding)
            except (UnicodeDecodeError, ValueError):
                continue
        raise ValueError("Не удалось декодировать .md файл — проверьте кодировку")


# ===================================================================
# Конвертер Pandoc grid-table → GFM pipe-table
# ===================================================================

def _split_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def _convert_grid_table_to_pipe(text: str) -> str:
    """
    Конвертирует Pandoc grid-tables (ASCII рамки +---+---+) в GFM pipe-tables.
    Это нужно, чтобы таблицы из Word-экспорта (pandoc) корректно
    рендерились react-markdown (remark-gfm).
    """
    lines = text.split("\n")
    out: list[str] = []
    i, n = 0, len(lines)

    while i < n:
        line = lines[i]
        if _GRID_BORDER.match(line):
            table_lines: list[str] = [line]
            i += 1
            while i < n:
                table_lines.append(lines[i])
                if _GRID_BORDER.match(lines[i]) and len(table_lines) > 1:
                    i += 1
                    if i < n and (_GRID_DATA.match(lines[i]) or _GRID_BORDER.match(lines[i])):
                        continue
                    break
                i += 1

            pipe_table = _grid_lines_to_pipe(table_lines)
            if pipe_table:
                out.append(pipe_table)
            else:
                out.extend(table_lines)
            continue

        out.append(line)
        i += 1

    return "\n".join(out)


def _grid_lines_to_pipe(table_lines: list[str]) -> str | None:
    """Parse grid-table lines into a GFM pipe-table string."""
    row_groups: list[list[str]] = []
    current: list[str] = []
    header_after: int | None = None

    for idx, line in enumerate(table_lines):
        if _GRID_BORDER.match(line):
            if current:
                row_groups.append(current)
                current = []
            if "=" in line and idx > 0:
                header_after = len(row_groups) - 1
        else:
            current.append(line)
    if current:
        row_groups.append(current)

    if not row_groups:
        return None

    pipe_rows: list[str] = []
    for group in row_groups:
        num_cols = len(_split_row(group[0]))
        merged_cells: list[list[str]] = [[] for _ in range(num_cols)]
        for line in group:
            cells = _split_row(line)
            for ci, cell in enumerate(cells):
                if ci < num_cols and cell.strip():
                    merged_cells[ci].append(cell.strip())
        row_text = "| " + " | ".join(
            " ".join(parts) if parts else ""
            for parts in merged_cells
        ) + " |"
        pipe_rows.append(row_text)

    if not pipe_rows:
        return None

    result: list[str] = []
    header_idx = header_after if header_after is not None else 0
    for ri, row in enumerate(pipe_rows):
        result.append(row)
        if ri == header_idx:
            num_cols = row.count("|") - 1
            result.append("| " + " | ".join(["---"] * max(num_cols, 1)) + " |")

    return "\n".join(result)


# ===================================================================
# Обработка inline-картинок
# ===================================================================

def _extract_images_inline(
    text: str,
) -> tuple[str, list[tuple[bytes, str]]]:
    """
    Обработка inline-картинок с сохранением позиции в тексте.

    - base64-картинки → байты сохраняются в список, в тексте ставится
      pending-b64:N маркер (потом заменяется на реальный URL)
    - обычные ссылки/пути → pending:imgN плейсхолдер
    """
    saved_images: list[tuple[bytes, str]] = []
    pending_counter = 0

    def _replace(m: re.Match) -> str:
        nonlocal pending_counter
        alt = m.group(1)
        src = m.group(2).strip().strip('"\'')
        data_match = _DATA_URI.match(src)

        if data_match:
            ext = data_match.group("ext").lower()
            ext = _EXT_ALIASES.get(ext, ext)
            if ext not in _ALLOWED_EXT:
                pending_counter += 1
                return f"![{alt}](pending:img{pending_counter})"

            try:
                raw = base64.b64decode(data_match.group("data"), validate=False)
            except Exception:
                pending_counter += 1
                return f"![{alt}](pending:img{pending_counter})"

            saved_images.append((raw, f".{ext}"))
            return f"![{alt}](pending-b64:{len(saved_images) - 1})"
        else:
            # Обычная ссылка / локальный путь — pending
            pending_counter += 1
            return f"![{alt}](pending:img{pending_counter})"

    text = _MD_IMAGE.sub(_replace, text)
    return text, saved_images


def finalize_question_md(
    text: str,
    images: list[tuple[bytes, str]],
    upload_dir: Path,
    question_id: int,
) -> tuple[str, list[str]]:
    """
    Финализирует markdown текста вопроса: заменяет pending-b64:N маркеры
    на реальные URL после сохранения файлов на диск.

    Возвращает: (финальный markdown, [relative_paths])
    """
    rel_paths: list[str] = []

    def _replace_pending(m: re.Match) -> str:
        alt = m.group(1)
        src = m.group(2)

        pb64_match = re.match(r'^pending-b64:(\d+)$', src)
        if pb64_match:
            idx = int(pb64_match.group(1))
            if idx < len(images):
                raw, ext = images[idx]
                if not ext.startswith("."):
                    ext = f".{ext}"
                safe_name = f"{uuid.uuid4().hex}{ext}"
                qdir = upload_dir / str(question_id)
                qdir.mkdir(parents=True, exist_ok=True)
                dest = qdir / safe_name
                dest.write_bytes(raw)
                rel_path = f"{question_id}/{safe_name}"
                rel_paths.append(rel_path)
                return f"![{alt}](/static/uploads/cert/{rel_path})"
        return m.group(0)

    text = _MD_IMAGE.sub(_replace_pending, text)
    return text, rel_paths


# ===================================================================
# Главный парсер: формат +++ / ..... / @
# ===================================================================

def parse_cert_md(
    raw_text: str,
) -> tuple[list[dict], list[tuple[bytes, str]]]:
    """
    Парсит .md файл в формате +++/...../@.

    Возвращает:
        (questions, images)

    questions — список dict:
        {
            "text": "markdown текст вопроса",
            "options": [
                {"text": "вариант 1", "is_correct": False},
                {"text": "@вариант 2", "is_correct": True},
                ...
            ],
            "needs_image": bool
        }

    images — список (bytes, ext) картинок, извлечённых из base64
    """
    # 1. Конвертируем grid-tables → pipe-tables
    text = _convert_grid_table_to_pipe(raw_text)

    # 2. Извлекаем base64-картинки → pending-b64:N маркеры
    text, images = _extract_images_inline(text)

    # 3. Нормализуем переносы строк
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 4. Разбиваем на блоки по +++
    blocks = _QUESTION_SEP.split(text)

    questions: list[dict] = []
    _pending_re = re.compile(r'!\[[^\]]*\]\(pending(?:-b64)?:[^)]+\)')

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Разбиваем блок по .....
        parts = _OPTION_SEP.split(block)
        parts = [p.strip() for p in parts if p.strip()]

        if len(parts) < 3:
            # Нужен минимум: вопрос + 2 варианта
            continue

        question_text = parts[0]
        needs_image = bool(_pending_re.search(question_text))

        options: list[dict] = []
        for raw_opt in parts[1:]:
            raw_opt = raw_opt.strip()
            if not raw_opt:
                continue

            is_correct = raw_opt.startswith(_CORRECT_MARK)
            if is_correct:
                raw_opt = raw_opt[1:].strip()  # убираем @

            if _pending_re.search(raw_opt):
                needs_image = True

            options.append({
                "text": raw_opt,
                "is_correct": is_correct,
            })

        if question_text and options:
            questions.append({
                "text": question_text,
                "options": options,
                "needs_image": needs_image,
            })

    if not questions:
        raise ValueError(
            "Не удалось найти ни одного задания.\n"
            "Формат .md для сертификата:\n"
            "+++\n"
            "Текст вопроса\n"
            ".....\n"
            "Вариант 1\n"
            ".....\n"
            "@Правильный вариант\n"
            ".....\n"
            "Вариант 3\n"
            ".....\n"
            "Вариант 4\n"
            "+++"
        )

    return questions, images

