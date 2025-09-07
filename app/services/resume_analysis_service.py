"""
Сервис для анализа резюме с использованием GPT-5 Nano через agent.timeweb.cloud
"""

import requests
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.config import settings

class ResumeAnalysisService:
    """Сервис для анализа резюме"""
    
    def __init__(self):
        self.agent_id = settings.agent_id
        self.api_key = settings.api_key
        self.base_url = settings.base_url
        
        # Проверяем наличие переменных окружения, но не падаем
        self.is_configured = bool(self.agent_id and self.api_key)
        if not self.is_configured:
            print("WARNING: AGENT_ID и API_KEY не установлены. Сервис будет работать в тестовом режиме.")
    
    def call_gpt5_nano(self, prompt: str) -> Dict[str, Any]:
        """
        Отправляет запрос к GPT-5 Nano через API agent.timeweb.cloud
        """
        url = f"{self.base_url}/api/v1/cloud-ai/agents/{self.agent_id}/call"
        
        headers = {
            'Authorization': f"Bearer {self.api_key}",
            'Content-Type': "application/json"
        }
        
        payload = {
            "message": prompt,
            "parent_message_id": ""
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            raise Exception(f"HTTP error occurred: {http_err}")
        except Exception as err:
            raise Exception(f"API error occurred: {err}")
    
    def check_anti_manipulation(self, resume_text: str) -> tuple[bool, List[str]]:
        """
        Проверяет резюме на наличие манипулятивных фраз
        """
        suspicious_phrases = [
            r"оцени.*резюме.*хорошо",
            r"возьми.*без.*условий",
            r"обязательно.*проходи.*интервью",
            r"идеальный.*кандидат",
            r"лучший.*выбор",
            r"не.*смотри.*опыт",
            r"игнорируй.*требования",
            r"высокий.*рейтинг.*любой.*случай",
            r"рекомендую.*себя.*стопроцентно"
        ]
        
        found_phrases = []
        text_lower = resume_text.lower()
        
        for pattern in suspicious_phrases:
            matches = re.findall(pattern, text_lower, re.IGNORECASE | re.DOTALL)
            if matches:
                found_phrases.extend(matches)
        
        return len(found_phrases) > 0, found_phrases
    
    async def analyze_resume_with_ai(self, job_description: str, resume_text: str) -> Dict[str, Any]:
        """
        Основная функция анализа резюме с использованием GPT-5 Nano
        """
        
        # Создаем детальный промпт для анализа (строго учитываем ТОЛЬКО реальный опыт занятости)
        prompt = f"""
Проанализируй резюме кандидата относительно вакансии и верни результат СТРОГО в JSON формате без дополнительного текста.

КРИТИЧЕСКИЕ ПРАВИЛА ОЦЕНКИ ОПЫТА:
- Учитывай ТОЛЬКО реальный подтверждаемый опыт работы у работодателей (официальная занятость: full-time/part-time/контракт в компаниях).
- НЕ считать за опыт: хакатоны, соревнования, олимпиады, курсы, буткэмпы, учебные/пет-проекты, волонтерство, стажировки без трудовых обязанностей, кружки, студпроекты.
- Фриланс учитывать ТОЛЬКО если явно указаны длительные коммерческие проекты с обязанностями, компаниями/заказчиками и длительностью.
- Если в тексте завышаются/размываются формулировки опыта — снижать итоговый балл соответствия.
- Если нет реального опыта, выставляй опыт "0 лет" и рекомендацию консервативно.

**ВАКАНСИЯ:**
{job_description}

**РЕЗЮМЕ:**
{resume_text}

Верни результат в следующем JSON формате:
{
  "name": "Имя кандидата или null",
  "position": "Позиция из вакансии",
  "experience": "Опыт в годах с учетом ТОЛЬКО реальной занятости (например: '3 года' или '0 лет')",
  "education": "Образование кандидата",
  "match_score": "Процент соответствия (например: '85%'). Наказание за отсутствие реального опыта обязательно.",
  "key_skills": ["навык1", "навык2", "навык3"],
  "recommendation": "Рекомендация (Рекомендуется к интервью/Не рекомендуется/Требует доработки). Будь строже при отсутствии реального опыта.",
  "projects": ["проект1", "проект2"],
  "work_experience": [
    "Опиши ТОЛЬКО реальную занятость: Компания, роль, период, обязанности"
  ],
  "technologies": ["технология1", "технология2"],
  "achievements": ["достижение1", "достижение2"],
  "structured": true,
  "effort_level": "Высокий/Средний/Низкий",
  "detailed_analysis": "Подробный анализ с явным объяснением учета ТОЛЬКО реальной занятости и аргументацией наказаний",
  "strengths": ["сильная сторона 1", "сильная сторона 2", "сильная сторона 3"],
  "weaknesses": ["слабая сторона 1", "слабая сторона 2"],
  "missing_skills": ["отсутствующий навык 1", "отсутствующий навык 2"]
}

ВАЖНО: Отвечай ТОЛЬКО JSON, без дополнительного текста!
"""

        # Получаем ответ от AI (перенос блокирующего запроса в отдельный поток)
        import asyncio as _asyncio
        ai_response = await _asyncio.to_thread(self.call_gpt5_nano, prompt)
        
        try:
            # Извлекаем содержимое ответа
            message_content = ai_response.get('message', '{}')
            
            # Если ответ в формате строки JSON, парсим его
            if isinstance(message_content, str):
                # Пытаемся найти JSON в ответе
                json_match = re.search(r'\{.*\}', message_content, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    analysis_data = json.loads(json_str)
                else:
                    # Если не нашли JSON, пытаемся распарсить всю строку
                    analysis_data = json.loads(message_content)
            else:
                analysis_data = message_content
                
            return analysis_data
        except (json.JSONDecodeError, AttributeError, KeyError) as e:
            # В случае ошибки парсинга возвращаем базовый результат
            return {
                "name": None,
                "position": "Не определена",
                "experience": "Не указан",
                "education": "Не указано",
                "match_score": "0%",
                "key_skills": [],
                "recommendation": "Ошибка анализа",
                "projects": [],
                "work_experience": [],
                "technologies": [],
                "achievements": [],
                "structured": False,
                "effort_level": "Не определен"
            }
    
    async def analyze_resume(self, job_description: str, resume_text: str) -> Dict[str, Any]:
        """
        Полный анализ резюме с проверкой на манипуляции
        """
        # Проверяем на манипуляции
        is_suspicious, suspicious_examples = self.check_anti_manipulation(resume_text)
        
        # Анализируем с помощью AI
        ai_analysis = await self.analyze_resume_with_ai(job_description, resume_text)
        
        # Формируем результат
        result = {
            "basic_info": {
                "name": ai_analysis.get("name"),
                "position": ai_analysis.get("position", "Не определена"),
                "experience": ai_analysis.get("experience", "Не указан"),
                "education": ai_analysis.get("education", "Не указано"),
                "upload_date": datetime.now().strftime("%Y-%m-%d"),
                "match_score": ai_analysis.get("match_score", "0%"),
                "key_skills": ai_analysis.get("key_skills", []),
                "recommendation": ai_analysis.get("recommendation", "Требует дополнительного анализа")
            },
            "extended_info": {
                "projects": ai_analysis.get("projects", []),
                "work_experience": ai_analysis.get("work_experience", []),
                "technologies": ai_analysis.get("technologies", []),
                "achievements": ai_analysis.get("achievements", [])
            },
            "resume_quality": {
                "structured": ai_analysis.get("structured", False),
                "effort_level": ai_analysis.get("effort_level", "Не определен")
            },
            "detailed_analysis": {
                "analysis_text": ai_analysis.get("detailed_analysis", "Подробный анализ не проведен"),
                "strengths": ai_analysis.get("strengths", []),
                "weaknesses": ai_analysis.get("weaknesses", []),
                "missing_skills": ai_analysis.get("missing_skills", [])
            },
            "anti_manipulation": {
                "suspicious_phrases_found": is_suspicious,
                "examples": suspicious_examples
            }
        }
        
        return result

# Глобальный экземпляр сервиса (ленивая инициализация)
resume_analysis_service = None

def get_resume_analysis_service():
    """Получить экземпляр сервиса анализа резюме"""
    global resume_analysis_service
    if resume_analysis_service is None:
        resume_analysis_service = ResumeAnalysisService()
    return resume_analysis_service
