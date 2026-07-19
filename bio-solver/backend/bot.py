import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
import os

# Инициализация бота
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://your-domain.com')  # URL вашего фронтенда

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🧬 Запустить BioSolver",
        web_app=WebAppInfo(url=WEBAPP_URL)
    )
    
    await message.answer(
        "👋 Привет! Я BioSolver - твой помощник для решения биологических задач!\n\n"
        "✨ Возможности:\n"
        "• Генетика (моно- и дигибридное скрещивание)\n"
        "• Биосинтез белка\n"
        "• Экологические пирамиды\n"
        "• Цитология\n\n"
        "Нажми кнопку ниже, чтобы запустить Mini App и начать решать задачи!",
        reply_markup=builder.as_markup()
    )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    await message.answer(
        "📚 **Как использовать BioSolver:**\n\n"
        "1. Нажми кнопку 'Запустить BioSolver'\n"
        "2. Выбери тип задачи из списка\n"
        "3. Заполни поля, используя специальную клавиатуру\n"
        "4. Нажми 'Сформировать решение'\n"
        "5. Отправь красивое решение ученику!\n\n"
        "⌨️ **Специальная клавиатура включает:**\n"
        "• Нуклеотиды: А, Т, Г, Ц, У\n"
        "• Генетические символы: X^A, X^a, ♀, ♂\n"
        "• Математические символы: индексы, греческие буквы\n\n"
        "💡 **Совет:** Используй режим нижнего/верхнего индекса для формул!"
    )

@dp.callback_query(lambda c: c.data == 'open_webapp')
async def process_callback_open_webapp(callback_query: types.CallbackQuery):
    """Обработчик нажатия на кнопку открытия WebApp"""
    await bot.answer_callback_query(callback_query.id)

def main():
    """Запуск бота"""
    print("🚀 BioSolver Bot запускается...")
    print(f"📱 WebApp URL: {WEBAPP_URL}")
    asyncio.run(dp.start_polling(bot))

if __name__ == "__main__":
    main()
