from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums import ChatType
from services.gigachat import GigaChatService
from utils.helpers import get_user_type, get_all_users_with_types, get_chat_messages_last_7_days, get_chat_members, save_report, get_today_report
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

    # Проверяем, не генерировался ли отчет сегодня
    existing_report = await get_today_report(message.chat.id)
    if existing_report:
        await message.answer(
            "📊 <b>Отчет уже генерировался сегодня!</b>\n\n"
            "Повторите команду /report завтра для получения нового анализа.",
            parse_mode="HTML"
        )
        return

    await message.answer("🔍 Начинаю анализ группы...")

    try:
        # Получаем участников чата из нашей базы
        chat_members = await get_chat_members(message.chat.id)
        
        if not chat_members:
            await message.answer(
                "❌ <b>Недостаточно данных для анализа</b>\n\n"
                "Бот должен накопить данные о сообщениях участников. "
                "Пожалуйста, подождите несколько дней активности в чате.",
                parse_mode="HTML"
            )
            return

        # Получаем всех пользователей с типированием из БД
        typed_users = await get_all_users_with_types()
        typed_user_ids = {user['user_id'] for user in typed_users}
        typed_users_dict = {user['user_id']: user for user in typed_users}

        # Анализируем участников
        typed_members = []
        untyped_members = []
        
        for member in chat_members:
            user_id = member['user_id']
            username = member['username'] or member['first_name']
            
            if user_id in typed_user_ids:
                personality_type = typed_users_dict[user_id]['personality_type']
                typed_members.append({
                    'username': f"@{username}" if member['username'] else username,
                    'type': personality_type
                })
            else:
                untyped_members.append(username)

        # Проверка 70% порога
        total_members = len(chat_members)
        typed_count = len(typed_members)
        
        if total_members == 0:
            await message.answer("❌ В группе нет участников для анализа.")
            return

        percentage = (typed_count / total_members) * 100
        
        # Показываем статистику
        stats_message = (
            f"📊 <b>Статистика группы \"{message.chat.title}\":</b>\n"
            f"Всего участников: {total_members}\n"
            f"Протестировано: {typed_count}\n"
            f"Процент: {percentage:.1f}%\n"
        )
        
        if typed_members:
            typed_list = "\n".join([f"• {m['username']}: {m['type']}" for m in typed_members])
            stats_message += f"\n<b>Протестированные участники:</b>\n{typed_list}"
        
        if untyped_members and len(untyped_members) <= 10:  # Показываем только если непротестированных не слишком много
            untyped_list = ", ".join(untyped_members[:10])
            if len(untyped_members) > 10:
                untyped_list += f" и еще {len(untyped_members) - 10}"
            stats_message += f"\n\n<b>Не протестированы:</b> {untyped_list}"

        await message.answer(stats_message, parse_mode="HTML")

        if percentage < 70:
            await message.answer(
                f"<b>📢 Для анализа необходимо чтобы >70% участников прошли тест</b>\n"
                f"<b>Непротестированные участники: {untyped_list}</b>\n"
                f"<b>Пройдите тест в личном чате с ботом:\n</b>"
                f"1. Перейдите в @SocioMind\n" 
                f"2. Отправьте команду /test\n\n"
                f"<i>Бот автоматически записывает активность в чате для будущего анализа</i>",
                parse_mode="HTML"
            )
            return

        await message.answer("🔮 <b>Анализирую динамику группы и сообщения за 7 дней...</b>", parse_mode="HTML")
        
        # Получаем историю сообщений за 7 дней
        chat_history = await get_chat_messages_last_7_days(message.chat.id)
        
        # Анализ группы с учетом истории сообщений
        analysis = await analyze_group_with_history(
            message, 
            typed_members, 
            total_members, 
            typed_count, 
            chat_history
        )
        
        # Сохраняем отчет
        await save_report(message.chat.id, analysis)
        await message.answer(analysis, parse_mode="HTML")
        
    except Exception as e:
        await message.answer(
            f"❌ Произошла ошибка при анализе группы: {str(e)}\n"
            f"Убедитесь, что бот имеет права администратора в группе."
        )
        print(f"Error in group analysis: {e}")

async def analyze_group_with_history(message: Message, typed_members: list, total_members: int, typed_count: int, chat_history: list) -> str:
    """Анализ группы с историей сообщений"""
    
    # Формируем текст истории для анализа
    history_text = ""
    if chat_history:
        # Группируем сообщения по пользователям
        user_messages = {}
        for msg in chat_history:
            user_id = msg['user_id']
            if user_id not in user_messages:
                user_messages[user_id] = []
            user_messages[user_id].append(msg['message_text'])
        
        # Создаем сводку по пользователям
        history_text = "История сообщений за 7 дней:\n"
        for user_id, messages in list(user_messages.items())[:10]:  # Ограничиваем для избежания переполнения
            user_info = next((m for m in typed_members if str(user_id) in m['username']), None)
            username = user_info['username'] if user_info else f"User_{user_id}"
            history_text += f"\n{username} ({len(messages)} сообщений):\n"
            # Берем последние 3 сообщения пользователя
            for msg in messages[-3:]:
                history_text += f"- {msg[:100]}{'...' if len(msg) > 100 else ''}\n"

    members_info = [f"• {m['username']}: {m['type']}" for m in typed_members]
    
    prompt = f"""
    Проанализируй динамику команды на основе типов личности участников и истории сообщений в чате за последние 7 дней.
    Дайте конкретные практические рекомендации по улучшению взаимодействия.

    ИНФОРМАЦИЯ О ГРУППЕ:
    - Название: "{message.chat.title}"
    - Всего участников: {total_members}
    - Протестированных: {typed_count}

    ТИПЫ ЛИЧНОСТИ УЧАСТНИКОВ:
    {chr(10).join(members_info)}

    ИСТОРИЯ СООБЩЕНИЙ ИЗ ЧАТА (последние 7 дней):
    {history_text}

    Будь максимально конкретен и дай практические, выполнимые рекомендации.
    Ответ должен быть структурированным и полезным для улучшения работы команды.

    ШАБЛОН ОТВЕТА (анализ должен быть в формате для parse_mode="HTML", вместо многоточий должен быть вставлен анализ):
    <b>Участники: </b>
    {chr(10).join(members_info)}
    🔍 <b>Наблюдения: </b>
    • ...
    • ...
    • ...
    • ...

    💡 <b>Рекомендации: </b>
    • ...
    • ...
    • ...

    ПРИМЕР ОТВЕТА:
    <b>Участники:</b>
    • @toxnela (ISFJ) - 45% сообщений
    • @riama_01 (INFJ) - 30% сообщений
    • @riama_01 (INTP) - 25% сообщений

    🔍 <b>Наблюдения: </b>
    • ISFJ: Стремится поддерживать дружественную атмосферу, чутко относится к потребностям окружающих.
    • INFJ: Глубоко задумчивый участник, ориентирован на выявление скрытого смысла и мотиваций собеседников.
    • INTP: Предпочитает логический анализ и теоретизацию, меньше заинтересован в социальных аспектах беседы.

    💡 <b>Рекомендации: </b>
    • ISFJ: Важно проявлять терпимость к различным стилям общения и позволять другим участникам выражать себя свободно, даже если это отличается от привычного подхода.
    • INFJ: Старайтесь уравновешивать глубину восприятия с ясностью изложения фактов, чтобы создать комфортную среду для обсуждения сложных вопросов.
    • INTP: Признавайте значимость личного опыта и чувств других членов команды, участвуйте в диалогах более открыто, демонстрируя уважение к ценностям коллег.
    """

    try:
        if gigachat_service.enabled:
            response = await gigachat_service.generate_group_analysis(prompt)
            return f"📊 <b>Отчет анализа группы \"{message.chat.title}\"</b>\n\n{response}"
        else:
            # Заглушка если GigaChat не доступен
            return f"""📊 <b>Отчет для группы "{message.chat.title}"</b>

👥 <b>Участники ({typed_count}/{total_members} протестированы):</b>
{chr(10).join(members_info)}

📝 <b>Анализ истории сообщений за 7 дней:</b>
{history_text[:500]}...

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