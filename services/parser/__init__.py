"""
services/parser/__init__.py
Фабрика: get_parser(filename) → нужный парсер.
Роутер просто вызывает:
    parser = get_parser(document.file_name)
    questions = await parser.parse(file_bytes)
"""
from services.parser.base import BaseParser
from services.parser.docx_parser import DocxParser
from services.parser.pdf_parser import PdfParser
from services.parser.txt_parser import TxtParser

_PARSERS: dict[str, BaseParser] = {
    ".txt":  TxtParser(),
    ".docx": DocxParser(),
    ".pdf":  PdfParser(),
}

SUPPORTED_EXTENSIONS = list(_PARSERS.keys())


def get_parser(filename: str) -> BaseParser:
    """
    Возвращает нужный парсер по расширению файла.
    Бросает ValueError если расширение не поддерживается.
    """
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    parser = _PARSERS.get(ext)
    if parser is None:
        supported = ", ".join(SUPPORTED_EXTENSIONS)
        raise ValueError(
            f"Формат «{ext}» не поддерживается. "
            f"Отправьте файл в одном из форматов: {supported}"
        )
    return parser


async def extract_text(filename: str, file_bytes: bytes) -> str:
    """
    Конвертирует файл (txt/docx/pdf) в plain text, без разбора на вопросы.
    Используется флешкартами — у них свой формат разбора (+++ и ===).
    """
    return await get_parser(filename)._to_text(file_bytes)
