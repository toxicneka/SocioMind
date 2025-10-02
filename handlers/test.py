from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.enums import ChatType
from aiogram.filters import Command
from config import questions
from utils.states import TestStates
from services.gigachat import GigaChatService
from services.google_sheets_service import GoogleSheetsService
from utils.helpers import save_user_type, get_user_type
from datetime import datetime
import asyncio

router = Router()
gigachat_service = GigaChatService()
sheets_service = GoogleSheetsService()

# Хранилище для ответов пользователей
user_answers = {}

# Команда /test работает ТОЛЬКО в личных сообщениях
@router.message(Command("test"), F.chat.type == ChatType.PRIVATE)
async def start_test(message: Message, state: FSMContext):
    # Проверяем, есть ли уже тип у пользователя
    existing_type = await get_user_type(message.from_user.id)
    if existing_type:
        await message.answer(
            f"📊 У вас уже определен тип: <b>{existing_type}</b>\n"
            "Начинаем новый тест...",
            parse_mode="HTML"
        )
    
    # Инициализируем или сбрасываем ответы пользователя
    user_answers[message.from_user.id] = []
    
    await message.answer(
        "📝 <b>Начинаем тестирование личности!</b>\n\n"
        "Ответьте на 8 вопросов. Будьте максимально искренни и отвечайте развернуто.\n"
        "Каждый ответ ограничен 500 символами.\n\n"
        "<i>Для отмены теста введите /cancel</i>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )
    await asyncio.sleep(1)
    await message.answer(f"1/8: {questions[0]}")
    await state.set_state(TestStates.waiting_for_answer_1)

@router.message(F.text == "/cancel")
async def cancel_test(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state and current_state.startswith("TestStates:"):
        if message.from_user.id in user_answers:
            del user_answers[message.from_user.id]
        await state.clear()
        await message.answer(
            "❌ Тест отменен. Ваши ответы не сохранены.",
            reply_markup=ReplyKeyboardRemove()
        )

# Обработчики для каждого вопроса (остаются без изменений)
@router.message(TestStates.waiting_for_answer_1, F.text)
async def process_answer_1(message: Message, state: FSMContext):
    if len(message.text) > 500:
        await message.answer("❌ Ответ слишком длинный. Сократите до 500 символов и отправьте снова.")
        return
        
    user_answers[message.from_user.id].append(message.text)
    await message.answer(f"2/8: {questions[1]}")
    await state.set_state(TestStates.waiting_for_answer_2)

@router.message(TestStates.waiting_for_answer_2, F.text)
async def process_answer_2(message: Message, state: FSMContext):
    if len(message.text) > 500:
        await message.answer("❌ Ответ слишком длинный. Сократите до 500 символов и отправьте снова.")
        return
        
    user_answers[message.from_user.id].append(message.text)
    await message.answer(f"3/8: {questions[2]}")
    await state.set_state(TestStates.waiting_for_answer_3)

@router.message(TestStates.waiting_for_answer_3, F.text)
async def process_answer_3(message: Message, state: FSMContext):
    if len(message.text) > 500:
        await message.answer("❌ Ответ слишком длинный. Сократите до 500 символов и отправьте снова.")
        return
        
    user_answers[message.from_user.id].append(message.text)
    await message.answer(f"4/8: {questions[3]}")
    await state.set_state(TestStates.waiting_for_answer_4)

@router.message(TestStates.waiting_for_answer_4, F.text)
async def process_answer_4(message: Message, state: FSMContext):
    if len(message.text) > 500:
        await message.answer("❌ Ответ слишком длинный. Сократите до 500 символов и отправьте снова.")
        return
        
    user_answers[message.from_user.id].append(message.text)
    await message.answer(f"5/8: {questions[4]}")
    await state.set_state(TestStates.waiting_for_answer_5)

@router.message(TestStates.waiting_for_answer_5, F.text)
async def process_answer_5(message: Message, state: FSMContext):
    if len(message.text) > 500:
        await message.answer("❌ Ответ слишком длинный. Сократите до 500 символов и отправьте снова.")
        return
        
    user_answers[message.from_user.id].append(message.text)
    await message.answer(f"6/8: {questions[5]}")
    await state.set_state(TestStates.waiting_for_answer_6)

@router.message(TestStates.waiting_for_answer_6, F.text)
async def process_answer_6(message: Message, state: FSMContext):
    if len(message.text) > 500:
        await message.answer("❌ Ответ слишком длинный. Сократите до 500 символов и отправьте снова.")
        return
        
    user_answers[message.from_user.id].append(message.text)
    await message.answer(f"7/8: {questions[6]}")
    await state.set_state(TestStates.waiting_for_answer_7)

@router.message(TestStates.waiting_for_answer_7, F.text)
async def process_answer_7(message: Message, state: FSMContext):
    if len(message.text) > 500:
        await message.answer("❌ Ответ слишком длинный. Сократите до 500 символов и отправьте снова.")
        return
        
    user_answers[message.from_user.id].append(message.text)
    await message.answer(f"8/8: {questions[7]}")
    await state.set_state(TestStates.waiting_for_answer_8)

@router.message(TestStates.waiting_for_answer_8, F.text)
async def process_answer_8(message: Message, state: FSMContext):
    if len(message.text) > 500:
        await message.answer("❌ Ответ слишком длинный. Сократите до 500 символов и отправьте снова.")
        return

    # Сохраняем последний ответ
    user_answers[message.from_user.id].append(message.text)
    
    await message.answer("🔮 <b>Анализирую ваши ответы...</b>", parse_mode="HTML")

    try:
        # Определение типа личности
        personality_type = await gigachat_service.determine_personality_type(
            user_answers[message.from_user.id]
        )
        
        # Проверяем, что тип определен корректно (содержит 4 буквы)
        if len(personality_type.strip()) != 4:
            personality_type = "INTJ"
            
        # Генерация развернутого анализа
        analysis = await gigachat_service.generate_personality_analysis(
            personality_type, 
            user_answers[message.from_user.id]
        )

        # Сохранение в БД
        await save_user_type(
            message.from_user.id,
            message.from_user.username or message.from_user.first_name,
            personality_type
        )

        # Сохранение в Google Sheets
        user_data = {
            'user_id': message.from_user.id,
            'username': message.from_user.username or message.from_user.first_name,
            'personality_type': personality_type,
            'timestamp': datetime.now().isoformat()
        }
        await sheets_service.save_to_sheets(user_data)

        # Отправляем результат пользователю
        await message.answer(
            f"🎯 <b>Ваш тип личности: {personality_type}</b>\n\n"
            f"{analysis}\n\n"
            f"<i>Теперь вы можете использовать команду /report в групповом чате для анализа команды</i>",
            parse_mode="HTML"
        )

    except Exception as e:
        await message.answer(
            "❌ Произошла ошибка при анализе. Попробуйте пройти тест позже.\n"
            f"Ошибка: {str(e)}"
        )
        print(f"Error in personality analysis: {e}")

    finally:
        # Очищаем состояние и удаляем ответы пользователя
        await state.clear()
        if message.from_user.id in user_answers:
            del user_answers[message.from_user.id]

# Обработчик для любого другого сообщения во время теста
@router.message(TestStates.waiting_for_answer_1)
@router.message(TestStates.waiting_for_answer_2)
@router.message(TestStates.waiting_for_answer_3)
@router.message(TestStates.waiting_for_answer_4)
@router.message(TestStates.waiting_for_answer_5)
@router.message(TestStates.waiting_for_answer_6)
@router.message(TestStates.waiting_for_answer_7)
@router.message(TestStates.waiting_for_answer_8)
async def process_wrong_input(message: Message):
    await message.answer(
        "❌ Пожалуйста, ответьте текстом на текущий вопрос.\n"
        "Ответ должен быть не более 500 символов.\n"
        "Для отмены теста введите /cancel"
    )