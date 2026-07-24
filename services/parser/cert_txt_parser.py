"""
services/parser/cert_txt_parser.py
Спец-парсер сертификационного теста.

Формат .md:
    +++
    Текст вопроса (markdown)
    .....
    Вариант 1
    .....
    @Вариант 2 (правильный)
    .....
    Вариант 3
    .....
    Вариант 4
    +++

Этот модуль принимает уже распарсенные вопросы из md_parser.parse_cert_md()
и конвертирует их в CertQuestionDraftDTO для сохранения через cert_service.
"""
import re

from dto.cert_dto import CertOptionDTO, CertQuestionDraftDTO

_PENDING_IMAGE = re.compile(r'!\[[^\]]*\]\(pending(?:-b64)?:[^)]+\)')


def questions_to_drafts(
    questions: list[dict],
    images: list[tuple[bytes, str]] | None = None,
) -> list[CertQuestionDraftDTO]:
    """
    Конвертирует список вопросов из parse_cert_md() в CertQuestionDraftDTO.

    questions — список dict из parse_cert_md():
        {"text": str, "options": [{"text": str, "is_correct": bool}], "needs_image": bool}

    images — список (bytes, ext) картинок, извлечённых из base64
    """
    drafts: list[CertQuestionDraftDTO] = []
    img_list = list(images) if images else []

    for q in questions:
        options = [
            CertOptionDTO(text=opt["text"], is_correct=opt["is_correct"])
            for opt in q["options"]
            if opt["text"]
        ]

        # Привязываем все картинки к первому вопросу
        draft = CertQuestionDraftDTO(
            text=q["text"],
            options=options,
            needs_image=q.get("needs_image", False),
            images=img_list,
        )
        drafts.append(draft)
        img_list = []  # картинки привязываются только к первому вопросу

    return drafts

