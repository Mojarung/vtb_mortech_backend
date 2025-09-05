"""
Интегрированный сервис для анализа резюме с использованием AI
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime

from app.services.ai_service import get_ai_service

from app.models.vacancy import Vacancy, VacancyApplication
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

import aiohttp

logger = logging.getLogger(__name__)

OCR_SERVICE_URL = os.getenv("OCR_SERVICE_URL", "http://localhost:8001")

class ResumeAnalysisService:
    """Сервис для полного анализа резюме"""
    
    @staticmethod
    async def analyze_resume_application(
        application: VacancyApplication, 
        vacancy: Vacancy, 
        candidate: User, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Полный анализ заявки с резюме
        """
        try:
            resume_text = await ResumeAnalysisService._extract_text_with_ocr(application.resume_file_path)
            
            if not resume_text or len(resume_text.strip()) < 50:
                logger.warning(f"Could not extract meaningful text from resume: {application.resume_file_path}")
                return await ResumeAnalysisService._create_fallback_analysis(application, db)
            
            ai_service = get_ai_service()
            vacancy_requirements = ResumeAnalysisService._format_vacancy_requirements(vacancy)
            ai_analysis = await ai_service.analyze_resume(resume_text, vacancy_requirements)
            resume_data = await ai_service.extract_resume_data(resume_text)
            await ResumeAnalysisService._update_application_with_analysis(
                application, ai_analysis, resume_data, db
            )
            
            return {
                "success": True,
                "analysis": ai_analysis,
                "resume_data": resume_data,
                "resume_text_length": len(resume_text)
            }
            
        except Exception as e:
            logger.error(f"Error in resume analysis: {e}")
            return await ResumeAnalysisService._create_fallback_analysis(application, db)
    
    @staticmethod
    async def _extract_text_with_ocr(pdf_path: str) -> str:
        """
        Извлекает текст из PDF с помощью OCR микросервиса
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_content = file.read()
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                data.add_field('file', pdf_content, filename=os.path.basename(pdf_path), content_type='application/pdf')
                async with session.post(f"{OCR_SERVICE_URL}/ocr/process-pdf", data=data, timeout=300) as resp:
                    if resp.status != 200:
                        logger.error(f"OCR service error: {resp.status} {await resp.text()}")
                        return ""
                    payload = await resp.json()
                    pages = payload.get('extracted_text', [])
                    full_text = "\n".join([p.get('text', '') for p in pages])
                    if full_text and len(full_text.strip()) > 50:
                        logger.info("Successfully extracted text using OCR microservice")
                        return full_text
                    return ""
        except Exception as e:
            logger.error(f"Error in OCR microservice call: {e}")
            return ""
    
    @staticmethod
    def _format_vacancy_requirements(vacancy: Vacancy) -> str:
        """Форматирует требования вакансии для AI анализа"""
        requirements = []
        
        if vacancy.title:
            requirements.append(f"Позиция: {vacancy.title}")
        
        if vacancy.experience_years:
            requirements.append(f"Требуемый опыт: {vacancy.experience_years} лет")
        
        if vacancy.requirements:
            requirements.append(f"Требования: {vacancy.requirements}")
        
        if vacancy.conditions:
            requirements.append(f"Условия: {vacancy.conditions}")
        
        if vacancy.about:
            requirements.append(f"Описание: {vacancy.about}")
        
        return "\n".join(requirements)
    
    @staticmethod
    async def _update_application_with_analysis(
        application: VacancyApplication,
        ai_analysis: Dict[str, Any],
        resume_data: Dict[str, Any],
        db: AsyncSession
    ):
        """Обновляет заявку с результатами AI анализа"""
        try:
            application.ai_recommendation = ai_analysis.get('recommendation', 'Анализ недоступен')
            application.ai_match_percentage = ai_analysis.get('match_percentage', 50)
            application.ai_analysis_date = datetime.utcnow()
            detailed_analysis = ai_analysis.get('detailed_analysis', '')
            strengths = ai_analysis.get('strengths', [])
            weaknesses = ai_analysis.get('weaknesses', [])
            analysis_notes = f"""
AI АНАЛИЗ РЕЗЮМЕ:

Рекомендация: {application.ai_recommendation}
Соответствие: {application.ai_match_percentage}%

СИЛЬНЫЕ СТОРОНЫ:
{chr(10).join(f"- {strength}" for strength in strengths)}

СЛАБЫЕ СТОРОНЫ:
{chr(10).join(f"- {weakness}" for weakness in weaknesses)}

ДЕТАЛЬНЫЙ АНАЛИЗ:
{detailed_analysis}

ИЗВЛЕЧЕННЫЕ ДАННЫЕ:
- Имя: {resume_data.get('name', 'Не определено')}
- Опыт: {resume_data.get('experience_years', 0)} лет
- Образование: {resume_data.get('education', 'Не указано')}
- Навыки: {', '.join(resume_data.get('skills', []))}
"""
            application.notes = analysis_notes
            await db.commit()
            await db.refresh(application)
        except Exception as e:
            logger.error(f"Error updating application with analysis: {e}")
            await db.rollback()
    
    @staticmethod
    async def _create_fallback_analysis(
        application: VacancyApplication, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Создает базовый анализ в случае ошибки"""
        try:
            application.ai_recommendation = "Требует ручной проверки"
            application.ai_match_percentage = 50
            application.ai_analysis_date = datetime.utcnow()
            application.notes = "Автоматический анализ недоступен. Требуется ручная проверка резюме."
            await db.commit()
            await db.refresh(application)
            return {"success": False, "error": "Could not analyze resume automatically", "fallback": True}
        except Exception as e:
            logger.error(f"Error creating fallback analysis: {e}")
            return {"success": False, "error": str(e), "fallback": False}
    
    @staticmethod
    async def batch_analyze_applications(
        applications: list[VacancyApplication],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Пакетный анализ нескольких заявок
        """
        try:
            ai_service = get_ai_service()
            batch_data = []
            for app in applications:
                if app.resume_file_path:
                    resume_text = await ResumeAnalysisService._extract_text_with_ocr(app.resume_file_path)
                    if resume_text and len(resume_text.strip()) > 50:
                        vacancy_result = await db.execute(
                            "SELECT * FROM vacancies WHERE id = %s", (app.vacancy_id,)
                        )
                        vacancy = vacancy_result.fetchone()
                        if vacancy:
                            vacancy_requirements = ResumeAnalysisService._format_vacancy_requirements(vacancy)
                            batch_data.append({
                                'application_id': app.id,
                                'resume_text': resume_text,
                                'vacancy_requirements': vacancy_requirements
                            })
            if not batch_data:
                return {"success": False, "error": "No valid resumes found for batch analysis"}
            results = await ai_service.batch_analyze_resumes(batch_data)
            updated_count = 0
            for i, result in enumerate(results):
                if i < len(batch_data):
                    app_id = batch_data[i]['application_id']
                    for app in applications:
                        if app.id == app_id:
                            await ResumeAnalysisService._update_application_with_analysis(
                                app, result, {}, db
                            )
                            updated_count += 1
                            break
            return {"success": True, "processed_count": len(batch_data), "updated_count": updated_count}
        except Exception as e:
            logger.error(f"Error in batch analysis: {e}")
            return {"success": False, "error": str(e)}
