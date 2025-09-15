import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from database.db_init import init_db
from handlers.start import start_router
from handlers.test import test_router
from middlewares.db import DbSessionMiddleware
from services.google_sheets import init_google_sheets
from services.rag import socio_rag  # Добавьте этот импорт

async def main():
    storage = MemoryStorage()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=storage)
    
    # Инициализация базы данных
    sessionmaker = await init_db()
    
    # Инициализация RAG
    await socio_rag.build_index('socio.txt')  # Добавьте эту строку
    
    # Добавляем middleware для работы с БД
    dp.update.middleware(DbSessionMiddleware(sessionmaker))
    
    # Регистрация роутеров
    dp.include_router(start_router)
    dp.include_router(test_router)
    
    print("🤖 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())