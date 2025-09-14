from google import genai
from config import GOOGLE_API_KEY
import asyncio

client = genai.Client(api_key=GOOGLE_API_KEY)

async def determine_personality_type(answers: list) -> str:
    try:
        # Формируем промпт для определения соционического типа
        prompt = f"""
        Проанализируй ответы пользователя на вопросы соционического теста и определи его тип личности по модели А.
        Ответы пользователя:
        {chr(10).join([f'{i+1}. {answer}' for i, answer in enumerate(answers)])}
        
        Определи соционический тип из следующих: 
        INTJ, INTP, ENTJ, ENTP, 
        INFJ, INFP, ENFJ, ENFP,
        ISTJ, ISFJ, ESTJ, ESFJ,
        ISTP, ISFP, ESTP, ESFP
        
        Верни только код типа личности (например: INTJ, ESFP и т.д.)
        """
        
        # Используем asyncio.to_thread для синхронного вызова
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: client.chats.create(model='gemini-2.0-flash').send_message(prompt)
        )
        
        return response.text.strip()
    except Exception as e:
        print(f"Error in determine_personality_type: {e}")
        raise