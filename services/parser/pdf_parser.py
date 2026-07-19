"""
services/parser/pdf_parser.py
Парсер .pdf — извлекаем текст через pdfminer.six,
передаём в базовый _parse_text().
"""
import io

from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams

from services.parser.base import BaseParser


class PdfParser(BaseParser):

    async def _to_text(self, file_bytes: bytes) -> str:
        try:
            input_buf  = io.BytesIO(file_bytes)
            output_buf = io.StringIO()

            extract_text_to_fp(
                input_buf,
                output_buf,
                laparams=LAParams(),
                output_type="text",
                codec="utf-8",
            )

            text = output_buf.getvalue().strip()
        except Exception as e:
            raise ValueError(f"Не удалось прочитать .pdf файл: {e}")

        if not text:
            raise ValueError(
                "PDF не содержит извлекаемого текста — возможно, это отсканированный документ"
            )

        return text
