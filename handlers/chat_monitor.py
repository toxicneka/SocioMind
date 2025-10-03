from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ChatType
from utils.helpers import save_chat_message, update_chat_member

router = Router()

@router.message(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def monitor_group_messages(message: Message):
    """Мониторинг сообщений в групповых чатах"""
    if message.text and not message.text.startswith('/'):
        try:
            # Сохраняем сообщение
            await save_chat_message(
                chat_id=message.chat.id,
                user_id=message.from_user.id,
                message_text=message.text
            )
            
            # Обновляем информацию об участнике
            await update_chat_member(
                chat_id=message.chat.id,
                user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name
            )
        except Exception as e:
            # Логируем ошибку, но не прерываем работу бота
            print(f"Ошибка при сохранении сообщения: {e}")