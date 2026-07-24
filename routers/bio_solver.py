"""
routers/bio_solver.py
Обработчики для команды /bio и кнопки «🧬 Bio Solver».
"""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from keyboards.main_kb import BTN_BIO
from webapp import runtime

router = Router()


@router.message(Command("bio"))
@router.message(F.text == BTN_BIO)
async def cmd_bio_solver(message: Message) -> None:
    base = runtime.get_webapp_url()
    if not base:
        await message.answer(
            "🧬 Bio Solver пока не доступен: нет публичного HTTPS-адреса Mini App."
        )
        return
    base = base.rstrip("/")

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🧬 Открыть Bio Solver (Mini App)",
                    web_app=WebAppInfo(url=f"{base}/bio"),
                )
            ]
        ]
    )

    text = (
        "🧬 <b>Bio Solver — Генетический калькулятор</b>\n\n"
        "Интерактивное решение генетических задач любой сложности:\n"
        "• Моно-, ди- и полигибридное скрещивание (1–5 генов)\n"
        "• Сцепленное наследование и кроссинговер (включая двойной)\n"
        "• Взаимодействие генов (эпистаз, комплементарность, полимерия)\n"
        "• Группы крови (система ABO и резус-фактор)\n"
        "• Плейотропия и летальные гены\n\n"
        "Нажми кнопку ниже, чтобы открыть калькулятор 👇"
    )

    await message.answer(text, reply_markup=kb)
