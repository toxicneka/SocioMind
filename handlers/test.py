import asyncio
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from utils.states import TestStates
from services.gemini import determine_personality_type
from services.google_sheets import init_google_sheets, save_to_sheets
from database.models import User, UserPersonality
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

test_router = Router()

questions = [
    "Опишите, как вы обычно реагируете на неожиданные изменения планов или нарушение привычного хода событий?",
    "Как вы проявляете креативность и находите нестандартные решения в рутинных или рабочих задачах?",
    "Как вы ведете себя в новой или незнакомой обстановке, чтобы произвести хорошее впечатление или адаптироваться?",
    "Что вас чаще всего выбивает из колеи или вызывает наибольшее напряжение в работе или общении?",
    "Какая поддержка или помощь со стороны других людей вызывает у вас чувство доверия и благодарности?",
    "На что вы обращаете внимание, когда оцениваете, насколько комфортно вам находиться в компании или с конкретным человеком?",
    "Как вы обычно реагируете, когда кто-то поступает, по вашему мнению, нерационально или неэффективно?",
    "Что вы делаете автоматически, не задумываясь, чтобы поддерживать порядок и комфорт вокруг себя или близких?"
]

@test_router.message(Command("test"))
async def cmd_test(message: Message, state: FSMContext, session: AsyncSession):
    # Проверка существующего типа
    result = await session.execute(
        select(User).where(User.telegram_id == message.from_user.id)
    )
    user = result.scalar_one_or_none()
    
    if user:
        # Проверяем, есть ли активная запись о личности
        result = await session.execute(
            select(UserPersonality)
            .where(UserPersonality.user_id == user.id)
            .order_by(UserPersonality.determined_at.desc())
        )
        latest_personality = result.scalar_one_or_none()
        
        if latest_personality:
            await message.answer(
                f"Ваш текущий тип: {latest_personality.personality_type}. Хотите перепройти тест? (Да/Нет)"
            )
            return
    
    # Если пользователя нет в базе, создаем его
    if not user:
        user = User(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    
    await message.answer("📝 Начинаем тестирование...")
    await state.update_data(answers=[], user_id=user.id)
    await state.set_state(TestStates.question_1)
    await message.answer(questions[0])

# Создаем обработчики для всех вопросов
def answer_handler(question_number: int):
    async def handler(message: Message, state: FSMContext, session: AsyncSession):
        data = await state.get_data()
        answers = data.get('answers', [])
        answers.append(message.text)
        await state.update_data(answers=answers)
        
        if question_number < len(questions):
            next_state = getattr(TestStates, f"question_{question_number + 1}")
            await state.set_state(next_state)
            await message.answer(questions[question_number])
        else:
            # Все ответы получены
            try:
                personality_type = await determine_personality_type(answers)
                
                # Сохранение в базу данных
                personality = UserPersonality(
                    user_id=data['user_id'],
                    personality_type=personality_type,
                    test_answers=answers
                )
                session.add(personality)
                await session.commit()
                
                # Сохранение в Google Sheets
                gc = init_google_sheets()
                await asyncio.to_thread(save_to_sheets, gc, {
                    'user_id': message.from_user.id,
                    'username': message.from_user.username,
                    'personality_type': personality_type
                })
                
                await message.answer(f"🔍 Ваш тип: {personality_type}")
            except Exception as e:
                await message.answer("❌ Произошла ошибка при определении типа личности. Пожалуйста, попробуйте позже.")
                print(f"Error determining personality type: {e}")
            finally:
                await state.clear()
    
    return handler

# Создаем обработчики для всех вопросов
for i in range(1, 9):
    test_router.message(getattr(TestStates, f"question_{i}"))(answer_handler(i))