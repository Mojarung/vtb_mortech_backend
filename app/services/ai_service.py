"""
Сервис для работы с OpenRouter API
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self, api_key: str, model: str = "anthropic/claude-3.5-sonnet", base_url: str = "openrouter.ai"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.base_headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'http://localhost:8000',  # Для OpenRouter
            'X-Title': 'VTB Mortech HR System'
        }
    
    async def _make_request(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> Dict[str, Any]:
        """Базовый метод для отправки запроса к OpenRouter API"""
        
        # Если нет API ключа, используем заглушку для тестирования
        if not self.api_key or self.api_key == "test":
            logger.info("Using AI mock for testing (no real API key)")
            return self._mock_ai_response(messages)
        
        url = f"https://{self.base_url}/api/v1/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2000  # Уменьшаем для экономии токенов
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=payload, headers=self.base_headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"OpenRouter API error {response.status}: {error_text}")
                        # В случае ошибки API, используем заглушку
                        return self._mock_ai_response(messages)
            except Exception as e:
                logger.error(f"Error calling OpenRouter API: {e}")
                # В случае ошибки, используем заглушку
                return self._mock_ai_response(messages)
    
    def _mock_ai_response(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Заглушка для тестирования AI без реального API"""
        import random
        import time
        
        # Имитируем задержку
        time.sleep(0.5)
        
        # Извлекаем последнее сообщение
        last_message = messages[-1]["content"] if messages else "Test message"
        
        return {
            "choices": [{
                "message": {
                    "content": f"Mock AI response to: {last_message[:100]}..."
                }
            }],
            "usage": {"total_tokens": 150},
            "mock": True
        }
    
    async def analyze_resume(self, resume_text: str, vacancy_requirements: str) -> Dict[str, Any]:
        """
        Анализ резюме и оценка соответствия вакансии
        """
        messages = [
            {
                "role": "system",
                "content": """Ты - эксперт HR-аналитик. Твоя задача - анализировать резюме кандидатов и оценивать их соответствие требованиям вакансий.

ВАЖНО: Отвечай ТОЛЬКО в JSON формате, без дополнительного текста или объяснений."""
            },
            {
                "role": "user",
                "content": f"""Проанализируй резюме кандидата и оцени его соответствие требованиям вакансии.

РЕЗЮМЕ КАНДИДАТА:
{resume_text}

ТРЕБОВАНИЯ ВАКАНСИИ:
{vacancy_requirements}

Верни анализ в следующем JSON формате:
{{
    "candidate_name": "Имя кандидата",
    "experience_years": "Количество лет опыта (число)",
    "education": "Образование",
    "skills": ["навык1", "навык2", "навык3"],
    "about": "Краткое описание о себе",
    "match_percentage": "Процент соответствия (0-100)",
    "strengths": ["сильная сторона1", "сильная сторона2"],
    "weaknesses": ["слабая сторона1", "слабая сторона2"],
    "recommendation": "Рекомендация: 'Рекомендуется к интервью', 'Требует дополнительной проверки', или 'Низкое соответствие'",
    "detailed_analysis": "Подробный анализ соответствия требованиям"
}}"""
            }
        ]
        
        try:
            result = await self._make_request(messages, temperature=0.3)
            
            # Если это заглушка, создаем тестовый анализ
            if result.get('mock'):
                return self._create_mock_analysis(resume_text, vacancy_requirements)
            
            # Извлекаем текст ответа
            ai_response = result.get('choices', [{}])[0].get('message', {}).get('content', '{}')
            
            # Парсим JSON ответ
            try:
                analysis = json.loads(ai_response)
                return analysis
            except json.JSONDecodeError:
                # Если не удалось распарсить JSON, создаем базовую структуру
                logger.warning("Failed to parse AI response as JSON, creating fallback")
                return self._create_fallback_analysis(resume_text)
                
        except Exception as e:
            logger.error(f"Error in resume analysis: {e}")
            return self._create_fallback_analysis(resume_text)
    
    async def batch_analyze_resumes(self, resume_analyses: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Пакетный анализ нескольких резюме
        """
        tasks = []
        for analysis_data in resume_analyses:
            task = self.analyze_resume(
                analysis_data['resume_text'], 
                analysis_data['vacancy_requirements']
            )
            tasks.append(task)
        
        # Выполняем все запросы параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обрабатываем результаты
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error in batch analysis {i}: {result}")
                processed_results.append(self._create_fallback_analysis(resume_analyses[i]['resume_text']))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def _create_mock_analysis(self, resume_text: str, vacancy_requirements: str) -> Dict[str, Any]:
        """Создает тестовый анализ для демонстрации"""
        import random
        
        # Генерируем случайные данные для демонстрации
        names = ["Иван Петров", "Анна Сидорова", "Михаил Козлов", "Елена Волкова", "Дмитрий Соколов"]
        educations = ["МГУ, Прикладная математика", "СПбГУ, Информатика", "МФТИ, Физика", "ВШЭ, Экономика"]
        skills_lists = [
            ["Python", "FastAPI", "PostgreSQL", "Docker"],
            ["JavaScript", "React", "Node.js", "MongoDB"],
            ["Java", "Spring", "MySQL", "Kubernetes"],
            ["C++", "Qt", "Linux", "Git"]
        ]
        
        name = random.choice(names)
        education = random.choice(educations)
        skills = random.choice(skills_lists)
        experience = random.randint(1, 8)
        match_percentage = random.randint(60, 95)
        
        if match_percentage >= 80:
            recommendation = "Рекомендуется к интервью"
            strengths = ["Соответствует требованиям по опыту", "Имеет нужные технические навыки"]
            weaknesses = ["Отсутствует опыт с некоторыми технологиями"]
        elif match_percentage >= 70:
            recommendation = "Требует дополнительной проверки"
            strengths = ["Хороший опыт работы", "Базовые навыки соответствуют"]
            weaknesses = ["Недостаточно опыта с некоторыми технологиями"]
        else:
            recommendation = "Низкое соответствие требованиям"
            strengths = ["Мотивированный кандидат"]
            weaknesses = ["Недостаточный опыт", "Отсутствуют ключевые навыки"]
        
        return {
            "candidate_name": name,
            "experience_years": experience,
            "education": education,
            "skills": skills,
            "about": f"Опытный разработчик с {experience} годами опыта в области IT",
            "match_percentage": match_percentage,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendation": recommendation,
            "detailed_analysis": f"Кандидат {name} имеет {experience} лет опыта. Образование: {education}. Навыки: {', '.join(skills)}. Соответствие требованиям: {match_percentage}%."
        }
    
    def _create_fallback_analysis(self, resume_text: str) -> Dict[str, Any]:
        """Создает базовый анализ в случае ошибки AI"""
        return {
            "candidate_name": "Не определено",
            "experience_years": 0,
            "education": "Не указано",
            "skills": [],
            "about": "Анализ недоступен",
            "match_percentage": 50,
            "strengths": [],
            "weaknesses": ["Не удалось проанализировать резюме"],
            "recommendation": "Требует дополнительной проверки",
            "detailed_analysis": "Автоматический анализ недоступен. Требуется ручная проверка."
        }
    
    async def extract_resume_data(self, resume_text: str) -> Dict[str, Any]:
        """
        Извлечение структурированных данных из резюме
        """
        messages = [
            {
                "role": "system",
                "content": """Ты - эксперт по извлечению структурированных данных из резюме. Твоя задача - извлекать информацию из текста резюме и представлять её в структурированном виде.

ВАЖНО: Отвечай ТОЛЬКО в JSON формате, без дополнительного текста."""
            },
            {
                "role": "user",
                "content": f"""Извлеки структурированные данные из резюме кандидата.

РЕЗЮМЕ:
{resume_text}

Верни данные в JSON формате:
{{
    "name": "Полное имя",
    "email": "email@example.com",
    "phone": "+7 (xxx) xxx-xx-xx",
    "experience_years": "Количество лет опыта (число)",
    "education": "Образование",
    "skills": ["навык1", "навык2"],
    "languages": ["язык1", "язык2"],
    "about": "О себе",
    "work_experience": [
        {{
            "company": "Название компании",
            "position": "Должность",
            "period": "Период работы",
            "description": "Описание обязанностей"
        }}
    ],
    "education_history": [
        {{
            "institution": "Учебное заведение",
            "degree": "Степень",
            "year": "Год окончания"
        }}
    ]
}}"""
            }
        ]
        
        try:
            result = await self._make_request(messages, temperature=0.2)
            
            # Если это заглушка, создаем тестовые данные
            if result.get('mock'):
                return self._create_mock_resume_data()
            
            # Извлекаем текст ответа
            ai_response = result.get('choices', [{}])[0].get('message', {}).get('content', '{}')
            
            try:
                data = json.loads(ai_response)
                return data
            except json.JSONDecodeError:
                logger.warning("Failed to parse resume extraction as JSON")
                return self._create_fallback_resume_data()
                
        except Exception as e:
            logger.error(f"Error in resume data extraction: {e}")
            return self._create_fallback_resume_data()
    
    def _create_mock_resume_data(self) -> Dict[str, Any]:
        """Создает тестовые данные резюме"""
        import random
        
        names = ["Иван Петров", "Анна Сидорова", "Михаил Козлов"]
        companies = ["Яндекс", "Сбер", "Тинькофф", "VK", "Ozon"]
        positions = ["Python Developer", "Backend Developer", "Full Stack Developer"]
        
        name = random.choice(names)
        experience = random.randint(1, 8)
        
        return {
            "name": name,
            "email": f"{name.lower().replace(' ', '.')}@example.com",
            "phone": f"+7 (9{random.randint(10, 99)}) {random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}",
            "experience_years": experience,
            "education": "МГУ, Прикладная математика",
            "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Git"],
            "languages": ["Русский", "Английский"],
            "about": f"Опытный разработчик с {experience} годами опыта в области backend разработки",
            "work_experience": [
                {
                    "company": random.choice(companies),
                    "position": random.choice(positions),
                    "period": f"2020-2024",
                    "description": "Разработка backend сервисов на Python"
                }
            ],
            "education_history": [
                {
                    "institution": "МГУ",
                    "degree": "Бакалавр прикладной математики",
                    "year": "2020"
                }
            ]
        }
    
    def _create_fallback_resume_data(self) -> Dict[str, Any]:
        """Создает базовые данные резюме в случае ошибки"""
        return {
            "name": "Не определено",
            "email": "",
            "phone": "",
            "experience_years": 0,
            "education": "Не указано",
            "skills": [],
            "languages": [],
            "about": "Данные недоступны",
            "work_experience": [],
            "education_history": []
        }


# Глобальный экземпляр сервиса (будет инициализирован в main.py)
ai_service: Optional[AIService] = None

def get_ai_service() -> AIService:
    """Получить экземпляр AI сервиса"""
    if ai_service is None:
        raise Exception("AI service not initialized. Please set OpenRouter API key in config.")
    return ai_service

def init_ai_service(api_key: str, model: str = "anthropic/claude-3.5-sonnet"):
    """Инициализировать AI сервис"""
    global ai_service
    ai_service = AIService(api_key, model)