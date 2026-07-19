"""
services/parser/txt_parser.py
Парсер .txt файлов — просто декодируем байты в строку.
Пробует UTF-8, при ошибке — cp1251 (часто используется в СНГ).
"""
from services.parser.base import BaseParser


class TxtParser(BaseParser):

    async def _to_text(self, file_bytes: bytes) -> str:
        for encoding in ("utf-8", "cp1251", "latin-1"):
            try:
                return file_bytes.decode(encoding)
            except (UnicodeDecodeError, ValueError):
                continue
        raise ValueError("Не удалось декодировать .txt файл — проверьте кодировку")
