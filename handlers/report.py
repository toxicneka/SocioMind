from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums import ChatType
from services.gigachat import GigaChatService
from utils.helpers import get_user_type, get_all_users_with_types
from datetime import datetime, timedelta
import asyncio

router = Router()
gigachat_service = GigaChatService()

@router.message(Command("report"), F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def cmd_report(message: Message):
    # Проверяем права администратора у бота
    try:
        bot_member = await message.bot.get_chat_member(message.chat.id, message.bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            await message.answer(
                "❌ <b>Для анализа группы бот должен быть администратором!</b>\n\n"
                "Предоставьте боту права администратора и попробуйте снова.",
                parse_mode="HTML"
            )
            return
    except Exception as e:
        await message.answer("❌ Не удалось проверить права бота. Убедитесь, что бот является администратором.")
        return

    await message.answer("🔍 Начинаю анализ группы...")

    try:
        # Получаем всех участников группы
        members = await get_all_group_members(message)
        
        if not members:
            await message.answer("❌ Не удалось получить информацию об участниках группы.")
            return

        # Получаем всех пользователей с типированием из БД
        typed_users = await get_all_users_with_types()
        typed_user_ids = {user['user_id'] for user in typed_users}
        typed_users_dict = {user['user_id']: user for user in typed_users}

        typed_members = 0
        members_info = []
        member_ids = set()
        
        for member in members:
            user_id = member.user.id
            if user_id in member_ids:
                continue
            member_ids.add(user_id)
            
            # Проверяем тип личности пользователя
            if user_id in typed_user_ids:
                typed_members += 1
                username = f"@{member.user.username}" if member.user.username else member.user.first_name
                personality_type = typed_users_dict[user_id]['personality_type']
                members_info.append(f"• {username}: {personality_type}")

        # Проверка 70% порога
        total_members = len(member_ids)
        if total_members == 0:
            await message.answer("❌ В группе нет участников для анализа.")
            return

        percentage = (typed_members / total_members) * 100
        
        # Показываем статистику
        stats_message = (
            f"📊 <b>Статистика группы \"{message.chat.title}\":</b>\n"
            f"Всего участников: {total_members}\n"
            f"Протестировано: {typed_members}\n"
            f"Процент: {percentage:.1f}%"
        )
        
        if members_info:
            stats_message += f"\n\n<b>Протестированные участники:</b>\n" + "\n".join(members_info)
        
        await message.answer(stats_message, parse_mode="HTML")

        if percentage < 70:
            await message.answer(
                f"❌ <b>Недостаточно данных для анализа</b>\n"
                f"Необходимо: >70% протестированных участников\n\n"
                f"Чтобы пройти тест, напишите боту @{(await message.bot.get_me()).username} команду /test",
                parse_mode="HTML"
            )
            return

        await message.answer("🔮 <b>Анализирую динамику группы и сообщения за 7 дней...</b>", parse_mode="HTML")
        
        # Получаем историю сообщений за 7 дней
        chat_history = await get_chat_history_last_7_days(message)
        
        # Анализ группы с учетом истории сообщений
        analysis = await analyze_group_messages(message, members_info, total_members, typed_members, chat_history)
        await message.answer(analysis, parse_mode="HTML")
        
    except Exception as e:
        await message.answer(
            f"❌ Произошла ошибка при анализе группы: {str(e)}\n"
            f"Убедитесь, что бот имеет права администратора в группе."
        )
        print(f"Error in group analysis: {e}")

async def get_all_group_members(message: Message):
    """Получение участников группы правильным способом"""
    members = []
    try:
        # Получаем администраторов - это всегда работает
        admins = await message.bot.get_chat_administrators(message.chat.id)
        for admin in admins:
            if not admin.user.is_bot:
                members.append(admin)
        
        # Дополнительно пытаемся получить информацию о других пользователях
        # через механизм упоминаний или известных ID
        # Это ограничение Telegram API:cite[4]
        
    except Exception as e:
        print(f"Ошибка получения участников: {e}")
    
    return members

async def get_chat_history_last_7_days(message: Message) -> str:
    """Получение доступной истории сообщений"""
    try:
        # В python-telegram-bot нет прямого доступа к полной истории
        # Можно получать только новые сообщения после запуска бота
        # Альтернатива - использовать Pyrogram:cite[2]
        
        messages_text = []
        # Этот метод будет работать только для сообщений, полученных после старта бота
        # Для полного доступа к истории рассмотрите переход на Pyrogram
        
        return "Для полного анализа истории сообщений необходимо использовать Pyrogram. Текущая библиотека предоставляет ограниченный доступ к истории."
        
    except Exception as e:
        print(f"Ошибка получения истории чата: {e}")
        return "Не удалось получить историю сообщений."

async def analyze_group_messages(message: Message, members_info: list, total_members: int, typed_members: int, chat_history: str) -> str:
    """Анализ группы с помощью GigaChat с учетом истории сообщений за 7 дней"""
    
    prompt = f"""
    Проанализируй динамику команды на основе типов личности участников и истории сообщений в чате за последние 7 дней.
    Дайте конкретные практические рекомендации по улучшению взаимодействия.

    ИНФОРМАЦИЯ О ГРУППЕ:
    - Название: "{message.chat.title}"
    - Всего участников: {total_members}
    - Протестированных: {typed_members}

    ТИПЫ ЛИЧНОСТИ УЧАСТНИКОВ:
    {chr(10).join(members_info)}

    ИСТОРИЯ СООБЩЕНИЙ ИЗ ЧАТА (последние 7 дней):
    {chat_history}

    ПРОАНАЛИЗИРУЙ и дай РЕКОМЕНДАЦИИ по:
    1. Коммуникационным паттернам между разными типами личности
    2. Потенциальным зонам конфликтов и как их избежать
    3. Оптимальному распределению ролей в команде
    4. Улучшению групповой динамики и сотрудничества
    5. Конкретным действиям для усиления сильных сторон команды

    Будь максимально конкретен и дай практические, выполнимые рекомендации.
    Ответ должен быть структурированным и полезным для улучшения работы команды.
    """

    try:
        if gigachat_service.enabled:
            response = await gigachat_service.generate_group_analysis(prompt)
            return response
        else:
            # Заглушка если GigaChat не доступен
            return f"""📊 <b>Отчет для группы "{message.chat.title}"</b>

👥 <b>Участники ({typed_members}/{total_members} протестированы):</b>
{chr(10).join(members_info)}

📝 <b>Анализ истории сообщений за 7 дней:</b>
{chat_history[:500]}...

💡 <b>Рекомендации (общие):</b>
• Создавайте сбалансированные рабочие пары, учитывая типы личности
• Организуйте регулярные ретроспективы для обсуждения коммуникации
• Используйте сильные стороны каждого типа при распределении задач
• Разработайте четкие процессы для минимизации конфликтов

🔮 <b>Для более детального анализа с AI:</b>
Настройте API ключ GigaChat в конфигурации бота"""
            
    except Exception as e:
        print(f"Ошибка анализа группы: {e}")
        return f"""📊 <b>Отчет для группы "{message.chat.title}"</b>

👥 <b>Состав группы:</b>
{chr(10).join(members_info)}

💡 <b>Общие рекомендации:</b>
• Учитывайте различия в коммуникационных стилях
• Создавайте разнообразные рабочие группы
• Поощряйте открытое обсуждение рабочих процессов
• Используйте сильные стороны каждого типа личности"""