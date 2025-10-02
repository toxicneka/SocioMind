import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from config import TOKEN

# Импорт handlers
from handlers.start import router as start_router
from handlers.test import router as test_router
from handlers.report import router as report_router
from handlers.group_commands import router as group_commands_router  # Новый обработчик

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Тест подключения к Google Sheets
    from services.google_sheets_service import GoogleSheetsService
    sheets_service = GoogleSheetsService()
    await sheets_service.test_connection()

    # Регистрация роутеров
    dp.include_router(start_router)
    dp.include_router(test_router)
    dp.include_router(report_router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())