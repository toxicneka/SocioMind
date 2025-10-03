import gspread
from google.oauth2.service_account import Credentials
import logging
from config import SPREADSHEET_ID, GOOGLE_SHEETS_CREDS
import asyncio
from datetime import datetime
import os

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class GoogleSheetsService:
    def __init__(self):
        self.enabled = False
        self.client = None
        self.sheet = None
        
        logger.info("=== НАЧАЛО ИНИЦИАЛИЗАЦИИ GOOGLE SHEETS ===")
        logger.info(f"GOOGLE_SHEETS_CREDS: {GOOGLE_SHEETS_CREDS}")
        logger.info(f"SPREADSHEET_ID: {SPREADSHEET_ID}")
        
        try:
            # Проверяем существование файла учетных данных
            if not GOOGLE_SHEETS_CREDS:
                logger.error("❌ GOOGLE_SHEETS_CREDS не указан в конфигурации")
                return
                
            if not os.path.exists(GOOGLE_SHEETS_CREDS):
                logger.error(f"❌ Файл {GOOGLE_SHEETS_CREDS} не найден!")
                return
            else:
                logger.info(f"✅ Файл {GOOGLE_SHEETS_CREDS} найден")
            
            # Проверяем SPREADSHEET_ID
            if not SPREADSHEET_ID:
                logger.error("❌ SPREADSHEET_ID не указан в конфигурации")
                return
            else:
                logger.info(f"✅ SPREADSHEET_ID указан: {SPREADSHEET_ID}")
            
            # Инициализация клиента с правильными scope
            # ДОБАВЬТЕ ЭТОТ SCOPE ДЛЯ GOOGLE DRIVE API
            scope = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            logger.info("🔑 Аутентификация с помощью service account...")
            
            creds = Credentials.from_service_account_file(GOOGLE_SHEETS_CREDS, scopes=scope)
            self.client = gspread.authorize(creds)
            logger.info("✅ Аутентификация успешна")
            
            # Открываем таблицу с обработкой ошибок
            logger.info("📊 Открываю таблицу...")
            try:
                spreadsheet = self.client.open_by_key(SPREADSHEET_ID)
                logger.info(f"✅ Таблица открыта: {spreadsheet.title}")
                
                # Получаем первый лист
                self.sheet = spreadsheet.sheet1
                logger.info("✅ Лист получен")
                
                self.enabled = True
                logger.info("🎉 GoogleSheetsService успешно инициализирован")
                
                # Инициализация заголовков
                asyncio.create_task(self.initialize_headers())
                
            except gspread.exceptions.SpreadsheetNotFound:
                logger.error("❌ Таблица не найдена. Проверьте SPREADSHEET_ID.")
            except gspread.exceptions.APIError as e:
                logger.error(f"❌ Ошибка API при открытии таблицы: {e}")
            
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при инициализации: {e}", exc_info=True)

    async def initialize_headers(self):
        """Инициализация заголовков таблицы"""
        try:
            if self.enabled:
                logger.info("📝 Проверяю заголовки таблицы...")
                existing_data = self.sheet.get_all_values()
                
                if not existing_data:
                    headers = ['User ID', 'Telegram username', 'Тип личности', 'Дата тестирования']
                    self.sheet.append_row(headers)
                    logger.info("✅ Заголовки таблицы инициализированы")
                else:
                    logger.info("ℹ️ Таблица уже содержит данные")
                    
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации заголовков: {e}")

    async def save_to_sheets(self, user_data: dict):
        """Сохранение данных пользователя в Google Sheets"""
        if not self.enabled:
            logger.warning(f"⚠️ Google Sheets отключен. Данные не сохранены: {user_data}")
            return
        
        try:
            logger.info(f"💾 Сохранение данных пользователя {user_data['user_id']}...")
            
            # Ищем существующего пользователя
            try:
                existing_user = self.sheet.find(str(user_data['user_id']))
                if existing_user:
                    row = existing_user.row
                    self.sheet.update(f'A{row}:D{row}', [[
                        user_data['user_id'],
                        user_data['username'],
                        user_data['personality_type'],
                        user_data.get('timestamp', datetime.now().isoformat())
                    ]])
                    logger.info(f"✅ Данные пользователя {user_data['user_id']} обновлены")
                else:
                    self.sheet.append_row([
                        user_data['user_id'],
                        user_data['username'],
                        user_data['personality_type'],
                        user_data.get('timestamp', datetime.now().isoformat())
                    ])
                    logger.info(f"✅ Данные пользователя {user_data['user_id']} добавлены")
                    
            except gspread.exceptions.CellNotFound:
                self.sheet.append_row([
                    user_data['user_id'],
                    user_data['username'],
                    user_data['personality_type'],
                    user_data.get('timestamp', datetime.now().isoformat())
                ])
                logger.info(f"✅ Данные пользователя {user_data['user_id']} добавлены (новый пользователь)")
                
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения в Google Sheets: {e}")

    async def test_connection(self):
        """Тест подключения к Google Sheets"""
        if not self.enabled:
            return False
        
        try:
            self.sheet.row_values(1)
            logger.info("✅ Тест подключения к Google Sheets пройден")
            return True
        except Exception as e:
            logger.error(f"❌ Тест подключения к Google Sheets не пройден: {e}")
            return False
