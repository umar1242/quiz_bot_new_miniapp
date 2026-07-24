"""
routers/cert.py
Команда /cert и кнопка «🎓 Сертификат» нижней навигации — открывает конструктор
(для создателя варианта) и список готовых вариантов «▶️ Пройти» (Mini App).
Плюс обработчики остальных кнопок нижней реплай-клавиатуры (main_kb) —
проксируют на существующие команды, чтобы навигация работала отовсюду.
"""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import CertVariantStatus
from keyboards.main_kb import BTN_CERT, BTN_DECKS, BTN_HOME, BTN_MYQUIZ, BTN_SETTINGS
from services import cert_service as cs
from webapp import runtime

router = Router()


@router.message(Command("create_quiz"))
async def cmd_create_quiz(message: Message) -> None:
    import os
    webapp_url = "http://localhost:8085"
    if os.path.exists("/tmp/creator_url.txt"):
        with open("/tmp/creator_url.txt", "r") as f:
            webapp_url = f.read().strip()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📝 Создать тест (Mini App)",
                web_app=WebAppInfo(url=webapp_url)
            )
        ]
    ])
    
    welcome_text = (
        "👋 <b>Добро пожаловать в Конструктор тестов!</b>\n\n"
        "Этот помощник позволит вам создать тест с формулами, картинками и таблицами, сгенерировать Markdown файл и скачать его.\n\n"
        "Нажмите кнопку ниже, чтобы запустить Mini App и начать создание тестов 👇"
    )
    await message.answer(welcome_text, reply_markup=kb, parse_mode="HTML")


@router.message(Command("cert"))
@router.message(F.text == BTN_CERT)
async def cmd_cert_menu(message: Message, db: AsyncSession) -> None:
    base = runtime.get_webapp_url()
    if not base:
        await message.answer(
            "🎓 Сертификационные тесты пока не настроены: нет публичного HTTPS-адреса Mini App. "
            "Включи туннель (TUNNEL_ENABLED=true) или задай WEBAPP_URL в .env."
        )
        return
    base = base.rstrip("/")

    variants = await cs.list_variants(db, message.from_user.id)
    ready = [v for v in variants if v.status == CertVariantStatus.ready]
    draft_count = len(variants) - len(ready)

    rows = [[InlineKeyboardButton(text="🛠 Открыть конструктор", web_app=WebAppInfo(url=base))]]
    for v in ready[:15]:
        rows.append([InlineKeyboardButton(
            text=f"▶️ Пройти «{v.title}»",
            web_app=WebAppInfo(url=f"{base}/?take={v.id}"),
        )])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)

    lines = ["🎓 <b>Сертификационные тесты</b>", ""]
    if ready:
        lines.append(f"Готово к прохождению: <b>{len(ready)}</b>")
    if draft_count:
        lines.append(f"В черновиках: <b>{draft_count}</b> — доредактируй в конструкторе.")
    if not variants:
        lines.append("Пока нет ни одного варианта — открой конструктор и импортируй первый.")
    lines.append("\nВыбери действие 👇")

    await message.answer("\n".join(lines), reply_markup=kb)


from keyboards.main_kb import BTN_BIO, BTN_CERT, BTN_DECKS, BTN_HOME, BTN_MYQUIZ, BTN_SETTINGS, BTN_ATF


# ---------------------------------------------------------------------------
# Остальные кнопки нижней навигации — проксируем на существующие команды.
# ---------------------------------------------------------------------------

@router.message(F.text == BTN_HOME)
async def kb_home(message: Message, db: AsyncSession, lang: str) -> None:
    from routers.start import _show_main_menu
    await _show_main_menu(message, message.from_user.id, db, lang)


@router.message(F.text == BTN_MYQUIZ)
async def kb_myquiz(message: Message, db: AsyncSession, lang: str) -> None:
    from routers.start import cmd_myquiz
    await cmd_myquiz(message, db, lang)


@router.message(F.text == BTN_DECKS)
async def kb_decks(message: Message, state: FSMContext, db: AsyncSession, lang: str) -> None:
    from routers.deck import cmd_flashcards
    await cmd_flashcards(message, state, db, lang)


@router.message(F.text == BTN_SETTINGS)
async def kb_settings(message: Message, lang: str) -> None:
    from routers.start import cmd_settings
    await cmd_settings(message, lang)


@router.message(F.text == BTN_BIO)
async def kb_bio(message: Message) -> None:
    from routers.bio_solver import cmd_bio_solver
    await cmd_bio_solver(message)


@router.message(F.text == BTN_ATF)
async def kb_atf(message: Message, state: FSMContext) -> None:
    from routers.atf_calculator import cmd_atf
    await cmd_atf(message, state)

