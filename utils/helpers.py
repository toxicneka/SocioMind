import aiosqlite
from typing import List, Dict
import logging

async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect('sociomind.db') as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS users
                          (user_id INTEGER PRIMARY KEY,
                           username TEXT,
                           personality_type TEXT,
                           test_date TEXT)''')
        await db.commit()

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