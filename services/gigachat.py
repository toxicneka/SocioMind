import aiofiles
import random
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from config import AU_TOKEN

class GigaChatService:
    def __init__(self):
        self.credentials = AU_TOKEN
        self.knowledge_base = None
        self.enabled = bool(AU_TOKEN and AU_TOKEN != "your_gigachat_api_key_here")

    async def load_knowledge_base(self):
        """Загрузка базы знаний соционики"""
        try:
            async with aiofiles.open('socio.txt', 'r', encoding='utf-8') as f:
                self.knowledge_base = await f.read()
        except Exception as e:
            print(f"Ошибка загрузки базы знаний: {e}")
            self.knowledge_base = "Базовые знания соционики"

    async def determine_personality_type(self, answers: list) -> str:
        """Определение типа личности на основе ответов"""
        if not self.enabled:
            return self._get_random_personality_type()
            
        if not self.knowledge_base:
            await self.load_knowledge_base()

        answers_text = "\n".join([f"{i+1}. {answer}" for i, answer in enumerate(answers)])
        
        prompt = f"""
        На основе базы знаний соционики и ответов пользователя определи соционический тип личности.
        Верни ТОЛЬКО аббревиатуру типа (например: INTJ, ENTP, ISFJ и т.д.) без каких-либо пояснений.

        База знаний соционики:
        {self.knowledge_base[:4000]}

        Ответы пользователя:
        {answers_text}

        Проанализируй ответы и определи тип по следующим критериям:
        - Экстраверсия (E) vs Интроверсия (I)
        - Сенсорика (S) vs Интуиция (N)  
        - Логика (T) vs Этика (F)
        - Рациональность (J) vs Иррациональность (P)

        Тип:
        """

        payload = Chat(
            messages=[
                Messages(role=MessagesRole.SYSTEM, content="Ты эксперт по соционике. Анализируй ответы и определяй тип личности. Возвращай ТОЛЬКО 4-буквенную аббревиатуру."),
                Messages(role=MessagesRole.USER, content=prompt)
            ],
            temperature=0.3,
            max_tokens=10
        )

        try:
            with GigaChat(credentials=self.credentials, verify_ssl_certs=False) as giga:
                response = giga.chat(payload)
                result = response.choices[0].message.content.strip()
                # Проверяем что результат - валидный тип личности
                if len(result) == 4 and result.isalpha():
                    return result
                else:
                    return self._get_random_personality_type()
        except Exception as e:
            print(f"Ошибка GigaChat: {e}")
            return self._get_random_personality_type()

    async def generate_personality_analysis(self, personality_type: str, answers: list) -> str:
        """Генерация развернутого анализа личности"""
        if not self.enabled:
            return self._get_stub_analysis(personality_type)
            
        if not self.knowledge_base:
            await self.load_knowledge_base()

        prompt = f"""
        На основе типа личности {personality_type} и базы знаний соционики, создай развернутый анализ личности.
        Опиши сильные стороны, зоны развития и рекомендации. Максимум 500 символов.

        База знаний:
        {self.knowledge_base[:3000]}

        Анализ для типа {personality_type}:
        """

        payload = Chat(
            messages=[
                Messages(role=MessagesRole.SYSTEM, content="Ты эксперт по соционике. Создавай точные и полезные анализы личности."),
                Messages(role=MessagesRole.USER, content=prompt)
            ],
            temperature=0.7,
            max_tokens=300
        )

        try:
            with GigaChat(credentials=self.credentials, verify_ssl_certs=False) as giga:
                response = giga.chat(payload)
                return response.choices[0].message.content
        except Exception as e:
            print(f"Ошибка GigaChat при анализе: {e}")
            return self._get_stub_analysis(personality_type)

    async def generate_group_analysis(self, prompt: str) -> str:
        """Генерация анализа группы с использованием RAG"""
        if not self.enabled:
            return "Анализ группы временно недоступен. Убедитесь, что настроен API ключ GigaChat."
        
        if not self.knowledge_base:
            await self.load_knowledge_base()

        # Добавляем базу знаний соционики в промпт для RAG
        enhanced_prompt = f"""
        {prompt}

        БАЗА ЗНАНИЙ ПО СОЦИОНИКЕ ДЛЯ АНАЛИЗА:
        {self.knowledge_base[:3000]}

        Проанализируй на основе приведенной базы знаний и дай конкретные рекомендации.
        """

        payload = Chat(
            messages=[
                Messages(role=MessagesRole.SYSTEM, content="Ты эксперт по командной динамике и соционике. Анализируй группы на основе типов личности и истории сообщений. Давай конкретные практические рекомендации."),
                Messages(role=MessagesRole.USER, content=enhanced_prompt)
            ],
            temperature=0.7,
            max_tokens=800
        )

        try:
            with GigaChat(credentials=self.credentials, verify_ssl_certs=False) as giga:
                response = giga.chat(payload)
                return response.choices[0].message.content
        except Exception as e:
            print(f"Ошибка GigaChat при анализе группы: {e}")
            return "Не удалось сгенерировать анализ группы. Проверьте настройки API."

    def _get_random_personality_type(self) -> str:
        """Генерация случайного типа личности для тестирования"""
        types = ['INTJ', 'INTP', 'ENTJ', 'ENTP', 
                'INFJ', 'INFP', 'ENFJ', 'ENFP',
                'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ', 
                'ISTP', 'ISFP', 'ESTP', 'ESFP']
        return random.choice(types)

    def _get_stub_analysis(self, personality_type: str) -> str:
        """Заглушка для анализа личности"""
        analyses = {
            'INTJ': 'Стратегический мыслитель с сильной волей. Сильные стороны: стратегическое планирование, независимость. Зоны развития: развитие эмпатии, гибкость в общении.',
            'INTP': 'Инновационный архитектор идей. Сильные стороны: логический анализ, креативность. Зоны развития: практическая реализация, эмоциональная вовлеченность.',
            'ENTJ': 'Решительный лидер. Сильные стороны: организация, принятие решений. Зоны развития: терпимость к ошибкам, эмпатия.',
            'ENTP': 'Изобретательный и находчивый. Сильные стороны: генерация идей, адаптивность. Зоны развития: завершение проектов, внимание к деталям.',
            'INFJ': 'Проницательный идеалист. Сильные стороны: понимание людей, видение будущего. Зоны развития: практичность, установление границ.',
            'INFP': 'Чуткий медиатор. Сильные стороны: ценности, креативность. Зоны развития: решительность, конфронтация.',
            'ENFJ': 'Вдохновляющий лидер. Сильные стороны: мотивация, коммуникация. Зоны развития: принятие критики, делегирование.',
            'ENFP': 'Энтузиаст-новатор. Сильные стороны: энтузиазм, связи с людьми. Зоны развития: фокусировка, рутина.',
            'ISTJ': 'Практичный реализатор. Сильные стороны: надежность, внимание к деталям. Зоны развития: гибкость, принятие рисков.',
            'ISFJ': 'Защитник-хранитель. Сильные стороны: преданность, практичность. Зоны развития: уверенность в себе, принятие изменений.',
            'ESTJ': 'Эффективный администратор. Сильные стороны: организация, решительность. Зоны развития: терпимость, эмпатия.',
            'ESFJ': 'Заботливый гармонизатор. Сильные стороны: социальность, практичность. Зоны развития: принятие критики, независимость.',
            'ISTP': 'Виртуоз-ремесленник. Сильные стороны: адаптивность, решение проблем. Зоны развития: планирование, эмоциональная экспрессия.',
            'ISFP': 'Гибкий художник. Сильные стороны: чувствительность, креативность. Зоны развития: конфронтация, структура.',
            'ESTP': 'Энергичный предприниматель. Сильные стороны: энергичность, практичность. Зоны развития: терпение, долгосрочное планирование.',
            'ESFP': 'Спонтанный развлекатель. Сильные стороны: энергичность, социальность. Зоны развития: глубина, планирование.'
        }
        return analyses.get(personality_type, f"Тип {personality_type} обладает уникальными характеристиками. Рекомендуется изучить особенности данного типа.")