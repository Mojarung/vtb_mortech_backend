"""
Сервис для анализа резюме с поддержкой провайдеров OpenRouter и Heroku AI (OpenAI-совместимый Chat Completions)
"""

import json
import re
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.config import settings


class ResumeAnalysisService:
    """Сервис для анализа резюме через выбранного AI-провайдера"""

    def __init__(self):
        # Конфиг читаем из settings
        self.provider = (settings.ai_provider or "openrouter").lower()

    def _build_request(self, prompt: str) -> tuple[str, Dict[str, str], Dict[str, Any]]:
        """Собирает URL, заголовки и payload под выбранного провайдера."""
        system_prompt = (
            "Ты профессиональный HR-аналитик. Анализируй резюме максимально точно и объективно."
        )

        if self.provider == "heroku":
            # Heroku AI Inference (OpenAI-совместимый)
            url = settings.heroku_ai_base_url or ""
            api_key = settings.heroku_ai_api_key or ""
            model = settings.heroku_ai_model or "gpt-4o-mini"

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 6000,
            }
            return url, headers, payload

        # По умолчанию — OpenRouter
        url = settings.openrouter_base_url or "https://openrouter.ai/api/v1/chat/completions"
        api_key = settings.openrouter_api_key or ""
        model = settings.openrouter_model or "deepseek/deepseek-r1:free"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        # Необязательные рекомендованные заголовки OpenRouter
        http_referer = settings.base_url or None
        if http_referer:
            headers["HTTP-Referer"] = http_referer
        headers["X-Title"] = "VTB Resume Analysis"

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 6000,
        }
        return url, headers, payload

    async def call_ai(self, prompt: str) -> str:
        """Вызывает AI API и возвращает контент ассистента (строка)."""
        url, headers, payload = self._build_request(prompt)

        print(f"🔍 AI Provider: {self.provider}")
        print(f"🔍 Request URL: {url}")
        print(f"🔍 Request Headers (masked auth): {{k: ('***' if k.lower()=='authorization' else v) for k,v in headers.items()}}")
        print(f"🔍 Request Payload: {payload}")

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                print(f"🔍 Response Status: {response.status_code}")
                print(f"🔍 Response Headers: {response.headers}")
                print(f"🔍 Response Body: {response.text}")

                response.raise_for_status()
                data = response.json()
                # Ожидаем OpenAI-совместимый формат
                return data["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                print(f"❌ HTTP Status Error: {e}")
                print(f"❌ Response Text: {e.response.text}")
                raise
            except Exception as e:
                print(f"❌ AI Provider API Error: {e}")
                raise
    
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
        Основная функция анализа резюме с использованием Open Router AI
        """
        
        prompt = (
            "Проанализируй резюме кандидата относительно вакансии и верни результат СТРОГО в JSON формате без дополнительного текста.\n\n"
            "КРИТИЧЕСКИЕ ПРАВИЛА ОЦЕНКИ ОПЫТА:\n"
            "- Учитывай ТОЛЬКО реальный подтверждаемый опыт работы у работодателей (официальная занятость: full-time/part-time/контракт в компаниях).\n"
            "- НЕ считать за опыт: хакатоны, соревнования, олимпиады, курсы, буткэмпы, учебные/пет-проекты, волонтерство, стажировки без трудовых обязанностей, кружки, студпроекты.\n"
            "- Фриланс учитывать ТОЛЬКО если явно указаны длительные коммерческие проекты с обязанностями, компаниями/заказчиками и длительностью.\n"
            "- Если в тексте завышаются/размываются формулировки опыта — снижать итоговый балл соответствия.\n"
            "- Если нет реального опыта, выставляй опыт \"0 лет\".\n"
            "- ВАЖНО: если в описании вакансии явно указано, что требуется 0 лет опыта, либо позиция \"junior/стажер\" — НЕ штрафуй кандидата за отсутствие коммерческого опыта. Оцени по навыкам, образованию и релевантности.\n\n"
            f"**ВАКАНСИЯ:**\n{job_description}\n\n"
            f"**РЕЗЮМЕ:**\n{resume_text}\n\n"
            "Верни результат в следующем JSON формате:\n"
            "{\n"
            "  \"name\": \"Имя кандидата или null\",\n"
            "  \"position\": \"Позиция из вакансии\",\n"
            "  \"experience\": \"Опыт в годах с учетом ТОЛЬКО реальной занятости (например: '3 года' или '0 лет')\",\n"
            "  \"education\": \"Образование кандидата\",\n"
            "  \"match_score\": \"Процент соответствия (например: '85%'). Если вакансия допускает 0 лет опыта, не штрафуй за отсутствие опыта.\",\n"
            "  \"key_skills\": [\"навык1\", \"навык2\", \"навык3\"],\n"
            "  \"recommendation\": \"Рекомендация (Рекомендуется к интервью/Не рекомендуется/Требует доработки). Если вакансия 0 лет опыта — оцени без штрафа.\",\n"
            "  \"projects\": [\"проект1\", \"проект2\"],\n"
            "  \"work_experience\": [\n"
            "    \"Опиши ТОЛЬКО реальную занятость: Компания, роль, период, обязанности\"\n"
            "  ],\n"
            "  \"technologies\": [\"технология1\", \"технология2\"],\n"
            "  \"achievements\": [\"достижение1\", \"достижение2\"],\n"
            "  \"structured\": true,\n"
            "  \"effort_level\": \"Высокий/Средний/Низкий\",\n"
            "  \"detailed_analysis\": \"Подробный анализ с явным объяснением учета ТОЛЬКО реальной занятости и аргументацией наказаний\",\n"
            "  \"strengths\": [\"сильная сторона 1\", \"сильная сторона 2\", \"сильная сторона 3\"],\n"
            "  \"weaknesses\": [\"слабая сторона 1\", \"слабая сторона 2\"],\n"
            "  \"missing_skills\": [\"отсутствующий навык 1\", \"отсутствующий навык 2\"]\n"
            "}\n\n"
            "ВАЖНО: Отвечай ТОЛЬКО JSON, без дополнительного текста!\n"
        )

        try:
            ai_response = await self.call_ai(prompt)
            
            # Извлекаем JSON из ответа
            json_match = re.search(r'\{[\s\S]*\}', ai_response)
            if json_match:
                json_str = json_match.group()
                analysis_data = json.loads(json_str)
            else:
                analysis_data = json.loads(ai_response)
            
            return analysis_data
        except Exception as e:
            print(f"Ошибка анализа резюме: {e}")
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
                "effort_level": "Не определен",
                "detailed_analysis": "Подробный анализ не проведен",
                "strengths": [],
                "weaknesses": [],
                "missing_skills": []
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
