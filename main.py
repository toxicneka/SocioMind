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

logging.basicConfig(level=logging.INFO)

async def scheduled_cleanup():
    """Периодическая очистка старых сообщений"""
    while True:
        await asyncio.sleep(24 * 60 * 60)  # 24 часа
        from utils.helpers import cleanup_old_messages
        await cleanup_old_messages()

async def main():
    bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Запускаем периодическую очистку
    asyncio.create_task(scheduled_cleanup())

    # Тест подключения к Google Sheets
    from services.google_sheets_service import GoogleSheetsService
    sheets_service = GoogleSheetsService()
    
    # ПРАВИЛЬНЫЙ ВЫЗОВ - убрал await так как test_connection синхронный
    if hasattr(sheets_service, 'test_connection'):
        sheets_service.test_connection()
    else:
        logging.warning("GoogleSheetsService не имеет метода test_connection")

    # Инициализация базы данных
    from utils.helpers import init_db
    await init_db()

    # Регистрация роутеров
    dp.include_router(start_router)
    dp.include_router(test_router)
    dp.include_router(report_router)
    
    # Добавляем мониторинг чатов (если файл существует)
    try:
        from handlers.chat_monitor import router as chat_monitor_router
        dp.include_router(chat_monitor_router)
        logging.info("✅ Chat monitor router загружен")
    except ImportError as e:
        logging.warning(f"⚠️ Chat monitor не загружен: {e}")

    logging.info("🤖 Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())