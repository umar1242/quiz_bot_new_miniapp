"""
routers/atf_calculator.py
Калькулятор задач по Энергетическому обмену и Фотосинтезу (Husniddin ATF-3)
Автоматическое решение задач 1-30 типов сборника Solijonov Husniddin
"""
import math
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

router = Router()

class ATFForm(StatesGroup):
    waiting_type1 = State()
    waiting_type3 = State()

def solve_atf_type1(diff_chala: float, diff_mit_cito_atf: float, diff_xloro_glukoza: float, ratio_xloro_mit: float = 30.0):
    """
    Решение Типа 1 (Задачи 1-10):
    - diff_chala: на сколько моль неполное > полное (k)
    - diff_mit_cito_atf: mit_atf - cito_total_atf
    - diff_xloro_glukoza: glukoza_xloro - glukoza_tot
    """
    # 36x - (2x + 2x + 2*diff_chala) = diff_mit_cito_atf
    # 32x - 2*diff_chala = diff_mit_cito_atf
    # 32x = diff_mit_cito_atf + 2*diff_chala
    x_tola = (diff_mit_cito_atf + 2 * diff_chala) / 32.0
    x_chala = x_tola + diff_chala
    tot_glukoza = x_tola + x_chala
    
    xloro_glukoza = tot_glukoza + diff_xloro_glukoza
    atf_for_glukoza = xloro_glukoza * 18.0
    
    mit_atf = 36.0 * x_tola
    tot_xloro_atf = mit_atf * ratio_xloro_mit
    
    percent_spent = (atf_for_glukoza / tot_xloro_atf) * 100.0 if tot_xloro_atf > 0 else 0.0
    
    return {
        "x_tola": x_tola,
        "x_chala": x_chala,
        "tot_glukoza": tot_glukoza,
        "xloro_glukoza": xloro_glukoza,
        "atf_for_glukoza": atf_for_glukoza,
        "mit_atf": mit_atf,
        "tot_xloro_atf": tot_xloro_atf,
        "percent_spent": percent_spent
    }

def solve_atf_type3(diff_water: float, diff_energy: float):
    """
    Решение Типа 3 (Задачи 21-30):
    - diff_water: fosforlanish_suv - oksidlanish_suv = 36x - 6x = 30x
    - diff_energy: mit_issiqlik - cito_atf = 1400x - 80x = 1320x (или соотв.)
    """
    x = diff_water / 30.0
    atf_spent = x * 18.0
    return {
        "x_tola": x,
        "atf_spent": atf_spent,
        "cito_atf_kj": x * 2 * 40,
        "mit_issiq_kj": x * 1400,
        "suv_fosfor": 36 * x,
        "suv_oksid": 6 * x
    }


@router.message(Command("atf"))
async def cmd_atf_menu(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ 1-Тип: АТФ митохондрий/цитоплазмы и хлоропласт", callback_data="atf_t1")],
        [InlineKeyboardButton(text="💧 3-Тип: Разница воды и энергии", callback_data="atf_t3")],
    ])
    text = (
        "📊 **Калькулятор задач по Энергетическому обмену (Husniddin ATF-3)**\n\n"
        "Выберите тип задачи из сборника Husniddin ATF-3:"
    )
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")


@router.callback_query(F.data == "atf_t1")
async def cb_atf_t1(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ATFForm.waiting_type1)
    await callback.message.answer(
        "📝 **Введите 3 числа через пробел для 1-Типа:**\n"
        "1. Разница глюкозы (неполное > полное, моль)\n"
        "2. Разница АТФ (митохондрии - цитоплазма)\n"
        "3. Разница глюкозы хлоропласта (хлоропласт - расщеплено)\n\n"
        "Пример: `4 88 62`"
    )
    await callback.answer()


@router.message(ATFForm.waiting_type1)
async def process_type1(message: Message, state: FSMContext):
    try:
        parts = [float(p) for p in message.text.split()]
        if len(parts) < 3:
            raise ValueError
        
        diff_chala, diff_atf, diff_glukoza = parts[:3]
        res = solve_atf_type1(diff_chala, diff_atf, diff_glukoza)
        
        text = (
            f"✅ **Пошаговое решение задачи (Тип 1):**\n\n"
            f"• Полностью расщепленная глюкоза: `{res['x_tola']:.1f} моль`\n"
            f"• Неполно расщепленная глюкоза: `{res['x_chala']:.1f} моль`\n"
            f"• Всего расщеплено глюкозы: `{res['tot_glukoza']:.1f} моль`\n"
            f"• Синтезировано глюкозы в хлоропластах: `{res['xloro_glukoza']:.1f} моль`\n\n"
            f"⚡ **АТФ и энергии:**\n"
            f"• АТФ на синтез глюкозы: `{res['atf_for_glukoza']:.0f} шт` ({res['xloro_glukoza']:.1f} × 18)\n"
            f"• АТФ в митохондриях: `{res['mit_atf']:.0f} шт`\n"
            f"• Всего АТФ в хлоропластах: `{res['tot_xloro_atf']:.0f} шт`\n\n"
            f"🎯 **Ответ:** **`{res['percent_spent']:.1f}%`** АТФ хлоропласта потрачено на синтез глюкозы."
        )
        await message.answer(text, parse_mode="Markdown")
        await state.clear()
    except Exception:
        await message.answer("❌ Ошибка ввода. Отправьте 3 числа через пробел, например: `4 88 62`")


@router.callback_query(F.data == "atf_t3")
async def cb_atf_t3(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ATFForm.waiting_type3)
    await callback.message.answer(
        "📝 **Введите 2 числа через пробел для 3-Типа:**\n"
        "1. Разница воды (фосфорилирование - окисление, моль)\n"
        "2. Разница энергии (митохондрии - цитоплазма, кДж)\n\n"
        "Пример: `106 2840`"
    )
    await callback.answer()


@router.message(ATFForm.waiting_type3)
async def process_type3(message: Message, state: FSMContext):
    try:
        parts = [float(p) for p in message.text.split()]
        if len(parts) < 2:
            raise ValueError
        diff_water, diff_energy = parts[:2]
        res = solve_atf_type3(diff_water, diff_energy)
        
        text = (
            f"✅ **Пошаговое решение задачи (Тип 3):**\n\n"
            f"• Полностью расщепленная глюкоза: `{res['x_tola']:.1f} моль`\n"
            f"• Вода при фосфорилировании (36x): `{res['suv_fosfor']:.1f} моль`\n"
            f"• Вода при окислении (6x): `{res['suv_oksid']:.1f} моль`\n\n"
            f"🎯 **Ответ:** Затрачено **`{res['atf_spent']:.0f} моль`** АТФ на синтез этой глюкозы."
        )
        await message.answer(text, parse_mode="Markdown")
        await state.clear()
    except Exception:
        await message.answer("❌ Ошибка ввода. Отправьте 2 числа через пробел, например: `106 2840`")
