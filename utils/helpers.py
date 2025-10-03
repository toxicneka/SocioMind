import aiosqlite
from typing import List, Dict
import logging

async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect('sociomind.db') as db:
        # Существующая таблица пользователей
        await db.execute('''CREATE TABLE IF NOT EXISTS users
                          (user_id INTEGER PRIMARY KEY,
                           username TEXT,
                           personality_type TEXT,
                           test_date TEXT)''')
        
        # Новая таблица для хранения сообщений чата
        await db.execute('''CREATE TABLE IF NOT EXISTS chat_messages
                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                           chat_id INTEGER,
                           user_id INTEGER,
                           message_text TEXT,
                           timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        
        # Новая таблица для отслеживания участников чата
        await db.execute('''CREATE TABLE IF NOT EXISTS chat_members
                          (chat_id INTEGER,
                           user_id INTEGER,
                           username TEXT,
                           first_name TEXT,
                           last_name TEXT,
                           first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                           last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                           PRIMARY KEY (chat_id, user_id))''')
        
        # Таблица для отчетов
        await db.execute('''CREATE TABLE IF NOT EXISTS reports
                          (chat_id INTEGER,
                           report_date DATE,
                           report_data TEXT,
                           PRIMARY KEY (chat_id, report_date))''')
        
        await db.commit()

async def save_chat_message(chat_id: int, user_id: int, message_text: str):
    """Сохранение сообщения чата"""
    async with aiosqlite.connect('sociomind.db') as db:
        await db.execute('''INSERT INTO chat_messages 
                          (chat_id, user_id, message_text) 
                          VALUES (?, ?, ?)''',
                       (chat_id, user_id, message_text))
        await db.commit()

async def update_chat_member(chat_id: int, user_id: int, username: str, first_name: str, last_name: str = None):
    """Обновление информации об участнике чата"""
    async with aiosqlite.connect('sociomind.db') as db:
        await db.execute('''INSERT OR REPLACE INTO chat_members 
                          (chat_id, user_id, username, first_name, last_name, last_seen) 
                          VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)''',
                       (chat_id, user_id, username, first_name, last_name))
        await db.commit()

async def get_chat_messages_last_7_days(chat_id: int) -> List[Dict]:
    """Получение сообщений чата за последние 7 дней"""
    async with aiosqlite.connect('sociomind.db') as db:
        cursor = await db.execute('''SELECT user_id, message_text, timestamp 
                                   FROM chat_messages 
                                   WHERE chat_id = ? 
                                   AND timestamp >= datetime('now', '-7 days')
                                   ORDER BY timestamp''', 
                                (chat_id,))
        results = await cursor.fetchall()
        return [{'user_id': row[0], 'message_text': row[1], 'timestamp': row[2]} for row in results]

async def get_chat_members(chat_id: int) -> List[Dict]:
    """Получение всех участников чата"""
    async with aiosqlite.connect('sociomind.db') as db:
        cursor = await db.execute('''SELECT user_id, username, first_name, last_name 
                                   FROM chat_members 
                                   WHERE chat_id = ?''', 
                                (chat_id,))
        results = await cursor.fetchall()
        return [{'user_id': row[0], 'username': row[1], 'first_name': row[2], 'last_name': row[3]} for row in results]

async def save_report(chat_id: int, report_data: str):
    """Сохранение отчета"""
    async with aiosqlite.connect('sociomind.db') as db:
        await db.execute('''INSERT OR REPLACE INTO reports 
                          (chat_id, report_date, report_data) 
                          VALUES (?, date('now'), ?)''',
                       (chat_id, report_data))
        await db.commit()

async def get_today_report(chat_id: int) -> str:
    """Получение сегодняшнего отчета"""
    async with aiosqlite.connect('sociomind.db') as db:
        cursor = await db.execute('''SELECT report_data FROM reports 
                                   WHERE chat_id = ? AND report_date = date('now')''',
                                (chat_id,))
        result = await cursor.fetchone()
        return result[0] if result else None

# Существующие функции оставляем без изменений
async def save_user_type(user_id: int, username: str, personality_type: str):
    """Сохранение типа пользователя в БД"""
    async with aiosqlite.connect('sociomind.db') as db:
        await db.execute('''INSERT OR REPLACE INTO users 
                          (user_id, username, personality_type, test_date)
                          VALUES (?, ?, ?, datetime('now'))''',
                       (user_id, username, personality_type))
        await db.commit()

async def get_user_type(user_id: int) -> str:
    """Получение типа пользователя"""
    async with aiosqlite.connect('sociomind.db') as db:
        cursor = await db.execute('SELECT personality_type FROM users WHERE user_id = ?', (user_id,))
        result = await cursor.fetchone()
        return result[0] if result else None

async def get_all_users_with_types() -> List[Dict]:
    """Получение всех пользователей с типами личности"""
    async with aiosqlite.connect('sociomind.db') as db:
        cursor = await db.execute('SELECT user_id, username, personality_type FROM users WHERE personality_type IS NOT NULL')
        results = await cursor.fetchall()
        return [{'user_id': row[0], 'username': row[1], 'personality_type': row[2]} for row in results]

async def cleanup_old_messages():
    """Очистка сообщений старше 7 дней"""
    async with aiosqlite.connect('sociomind.db') as db:
        await db.execute("DELETE FROM chat_messages WHERE timestamp < datetime('now', '-7 days')")
        await db.commit()
        logging.info("✅ Сообщения старше 7 дней очищены")