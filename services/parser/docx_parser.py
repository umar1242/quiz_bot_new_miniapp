"""
services/parser/docx_parser.py
Парсер .docx — извлекаем параграфы через python-docx,
склеиваем в plain text и передаём в базовый _parse_text().
"""
import io

from docx import Document

from services.parser.base import BaseParser


class DocxParser(BaseParser):

    async def _to_text(self, file_bytes: bytes) -> str:
        try:
            doc = Document(io.BytesIO(file_bytes))
        except Exception as e:
            raise ValueError(f"Не удалось открыть .docx файл: {e}")

        lines: list[str] = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                lines.append(text)

        if not lines:
            raise ValueError("Документ .docx пустой или содержит только изображения")

        return "\n".join(lines)
