from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart

start_router = Router()

@start_router.message(CommandStart())
async def cmd_start(message: Message):
    welcome_text = """
👋 Привет! Я SocioMind AI Agent - бот для анализа командной совместимости на основе соционики.

📌 Мои возможности:
• Определение вашего соционического типа (/test)
• Анализ групповой динамики (/report)
• Рекомендации по улучшению взаимодействия

⚠️ Для группового анализа необходимо:
• Добавить меня в чат и дать права администратора
• более 70% участников прошли тест

▶️ Доступные команды:
/test - пройти тестирование личности
/report - получить анализ группы (только после теста)
    """
    await message.answer(welcome_text)