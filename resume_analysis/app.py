from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv
import re
from typing import List, Dict, Any, Optional

# Загружаем переменные окружения
load_dotenv()

app = FastAPI(title="Resume Analyzer API", version="1.0.0")

# Конфигурация из .env
AGENT_ID = os.getenv("AGENT_ID")
API_KEY = os.getenv("API_KEY") 
BASE_URL = os.getenv("BASE_URL", "https://agent.timeweb.cloud")
print("Загруженные переменные:")
print(f"AGENT_ID: {AGENT_ID}")
print(f"API_KEY: {'*' * 10 if API_KEY else None}")
print(f"BASE_URL: {BASE_URL}")


# Проверяем наличие обязательных переменных
if not AGENT_ID or not API_KEY:
    raise ValueError("AGENT_ID и API_KEY должны быть установлены в .env файле")

# Модели данных
class ResumeAnalyzeRequest(BaseModel):
    job_description: str
    resume_text: str

class BasicInfo(BaseModel):
    name: Optional[str] = None
    position: Optional[str] = None
    experience: Optional[str] = None
    education: Optional[str] = None
    upload_date: str
    match_score: str
    key_skills: List[str]
    recommendation: str

class ExtendedInfo(BaseModel):
    projects: List[str]
    work_experience: List[str]
    technologies: List[str]
    achievements: List[str]

class ResumeQuality(BaseModel):
    structured: bool
    effort_level: str

class AntiManipulation(BaseModel):
    suspicious_phrases_found: bool
    examples: List[str]

class ResumeAnalyzeResponse(BaseModel):
    basic_info: BasicInfo
    extended_info: ExtendedInfo
    resume_quality: ResumeQuality
    anti_manipulation: AntiManipulation

def call_gpt5_nano(prompt: str) -> Dict[str, Any]:
    """
    Отправляет запрос к GPT-5 Nano через API agent.timeweb.cloud
    """
    url = f"{BASE_URL}/api/v1/cloud-ai/agents/{AGENT_ID}/call"
    
    headers = {
        'Authorization': f"Bearer {API_KEY}",
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
        raise HTTPException(status_code=500, detail=f"HTTP error occurred: {http_err}")
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"API error occurred: {err}")

def check_anti_manipulation(resume_text: str) -> tuple[bool, List[str]]:
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

async def analyze_resume_with_ai(job_description: str, resume_text: str) -> Dict[str, Any]:
    """
    Основная функция анализа резюме с использованием GPT-5 Nano
    """
    
    # Создаем детальный промпт для анализа
    prompt = f"""
Проанализируй резюме кандидата относительно вакансии и верни результат СТРОГО в JSON формате без дополнительного текста.

**ВАКАНСИЯ:**
{job_description}

**РЕЗЮМЕ:**
{resume_text}

Верни результат в следующем JSON формате:
{{
  "name": "Имя кандидата или null",
  "position": "Позиция из вакансии",
  "experience": "Опыт в годах (например: '3 года')",
  "education": "Образование кандидата",
  "match_score": "Процент соответствия (например: '85%')",
  "key_skills": ["навык1", "навык2", "навык3"],
  "recommendation": "Рекомендация (Рекомендуется к интервью/Не рекомендуется/Требует доработки)",
  "projects": ["проект1", "проект2"],
  "work_experience": ["опыт1", "опыт2"],
  "technologies": ["технология1", "технология2"],
  "achievements": ["достижение1", "достижение2"],
  "structured": true,
  "effort_level": "Высокий/Средний/Низкий"
}}

ВАЖНО: Отвечай ТОЛЬКО JSON, без дополнительного текста!
"""

    # Получаем ответ от AI
    ai_response = call_gpt5_nano(prompt)
    
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

@app.get("/")
async def root():
    return {"message": "Resume Analyzer API is running"}

@app.post("/analyze_resume", response_model=ResumeAnalyzeResponse)
async def analyze_resume(request: ResumeAnalyzeRequest):
    """
    Анализирует резюме относительно вакансии
    """
    
    # Проверяем входные данные
    if not request.job_description.strip():
        raise HTTPException(status_code=400, detail="job_description не может быть пустым")
    
    if not request.resume_text.strip():
        raise HTTPException(status_code=400, detail="resume_text не может быть пустым")
    
    try:
        # Проверяем на манипуляции
        is_suspicious, suspicious_examples = check_anti_manipulation(request.resume_text)
        
        # Анализируем с помощью AI
        ai_analysis = await analyze_resume_with_ai(request.job_description, request.resume_text)
        
        # Формируем результат
        result = ResumeAnalyzeResponse(
            basic_info=BasicInfo(
                name=ai_analysis.get("name"),
                position=ai_analysis.get("position", "Не определена"),
                experience=ai_analysis.get("experience", "Не указан"),
                education=ai_analysis.get("education", "Не указано"),
                upload_date=datetime.now().strftime("%Y-%m-%d"),
                match_score=ai_analysis.get("match_score", "0%"),
                key_skills=ai_analysis.get("key_skills", []),
                recommendation=ai_analysis.get("recommendation", "Требует дополнительного анализа")
            ),
            extended_info=ExtendedInfo(
                projects=ai_analysis.get("projects", []),
                work_experience=ai_analysis.get("work_experience", []),
                technologies=ai_analysis.get("technologies", []),
                achievements=ai_analysis.get("achievements", [])
            ),
            resume_quality=ResumeQuality(
                structured=ai_analysis.get("structured", False),
                effort_level=ai_analysis.get("effort_level", "Не определен")
            ),
            anti_manipulation=AntiManipulation(
                suspicious_phrases_found=is_suspicious,
                examples=suspicious_examples
            )
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа резюме: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
