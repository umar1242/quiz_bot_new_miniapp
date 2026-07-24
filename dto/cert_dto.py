"""
dto/cert_dto.py
Промежуточные структуры для сертификационных тестов (парсер → cert_service → БД).
"""
from dataclasses import dataclass, field


@dataclass
class CertOptionDTO:
    text: str
    is_correct: bool = False


@dataclass
class CertQuestionDraftDTO:
    """Черновик задания Y1, полученный из спец-парсера сертификационного теста."""
    text: str
    options: list[CertOptionDTO] = field(default_factory=list)
    needs_image: bool = False
    # Картинки, уже извлечённые парсером (например, base64 из markdown) —
    # каждая как (байты файла, расширение с точкой, напр. ".png").
    images: list[tuple[bytes, str]] = field(default_factory=list)
