"""
API роутер для управления заявками на вакансии
"""

import os
import uuid
import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import User, Vacancy, VacancyApplication
from app.schemas.vacancy import (
    VacancyApplicationRead,
    VacancyApplicationUpdate,
    VacancyApplicationWithDetails,
    ApplicationStatusUpdate,
    InterviewSchedule
)
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/applications", tags=["applications"])


async def analyze_resume_with_ai(application: VacancyApplication, vacancy: Vacancy, candidate: User, db: AsyncSession):
    """
    AI анализ резюме с использованием OpenRouter
    """
    try:
        from app.services.resume_analysis_service import ResumeAnalysisService
        
        # Выполняем полный анализ резюме
        result = await ResumeAnalysisService.analyze_resume_application(
            application, vacancy, candidate, db
        )
        
        if result.get("success"):
            logger.info(f"Successfully analyzed resume for application {application.id}")
        else:
            logger.warning(f"Resume analysis failed for application {application.id}: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error in AI resume analysis: {e}")
        # В случае ошибки создаем базовый анализ
        application.ai_recommendation = "Анализ недоступен"
        application.ai_match_percentage = 50
        application.ai_analysis_date = datetime.utcnow()
        application.notes = "Ошибка автоматического анализа. Требуется ручная проверка."
        
        await db.commit()
        await db.refresh(application)


@router.post("/apply/{vacancy_id}", response_model=VacancyApplicationRead, status_code=status.HTTP_201_CREATED)
async def apply_to_vacancy(
    vacancy_id: int,
    resume_file: UploadFile = File(..., description="PDF файл резюме"),
    cover_letter: str = Form(None, description="Сопроводительное письмо"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Подача заявки на вакансию с резюме
    """
    # Проверяем, что пользователь не HR
    if current_user.is_hr:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="HR не могут подавать заявки на вакансии"
        )
    
    # Проверяем существование вакансии
    result = await db.execute(select(Vacancy).where(Vacancy.id == vacancy_id))
    vacancy = result.scalar_one_or_none()
    
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вакансия не найдена"
        )
    
    # Проверяем, не подавал ли уже заявку
    existing_application = await db.execute(
        select(VacancyApplication).where(
            VacancyApplication.vacancy_id == vacancy_id,
            VacancyApplication.candidate_id == current_user.id
        )
    )
    
    if existing_application.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вы уже подавали заявку на эту вакансию"
        )
    
    # Валидация файла
    if not resume_file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поддерживаются только PDF файлы"
        )
    
    if resume_file.size and resume_file.size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Размер файла не должен превышать 10MB"
        )
    
    try:
        # Создаем директорию для загрузок
        upload_dir = "uploads/resumes"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Генерируем уникальное имя файла
        file_extension = resume_file.filename.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Сохраняем файл
        with open(file_path, "wb") as buffer:
            content = await resume_file.read()
            buffer.write(content)
        
        # Создаем заявку
        application = VacancyApplication(
            vacancy_id=vacancy_id,
            candidate_id=current_user.id,
            resume_file_path=file_path,
            resume_file_name=resume_file.filename,
            resume_file_size=len(content),
            cover_letter=cover_letter,
            status="pending"
        )
        
        db.add(application)
        await db.commit()
        await db.refresh(application)
        
        # Запускаем AI анализ в фоне
        try:
            await analyze_resume_with_ai(application, vacancy, current_user, db)
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
        
        return application
        
    except Exception as e:
        # Удаляем файл в случае ошибки
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        
        logger.error(f"Error creating application: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании заявки"
        )


@router.get("/my", response_model=List[VacancyApplicationWithDetails])
async def get_my_applications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение заявок текущего пользователя
    """
    result = await db.execute(
        select(VacancyApplication, Vacancy)
        .join(Vacancy, VacancyApplication.vacancy_id == Vacancy.id)
        .where(VacancyApplication.candidate_id == current_user.id)
        .order_by(VacancyApplication.applied_at.desc())
    )
    
    applications = []
    for application, vacancy in result:
        app_data = {
            "id": application.id,
            "vacancy_id": application.vacancy_id,
            "candidate_id": application.candidate_id,
            "status": application.status,
            "cover_letter": application.cover_letter,
            "notes": application.notes,
            "resume_file_path": application.resume_file_path,
            "resume_file_name": application.resume_file_name,
            "resume_file_size": application.resume_file_size,
            "ai_recommendation": application.ai_recommendation,
            "ai_match_percentage": application.ai_match_percentage,
            "ai_analysis_date": application.ai_analysis_date,
            "interview_date": application.interview_date,
            "interview_link": application.interview_link,
            "interview_notes": application.interview_notes,
            "applied_at": application.applied_at,
            "status_updated_at": application.status_updated_at,
            "vacancy": {
                "id": vacancy.id,
                "title": vacancy.title,
                "company_name": vacancy.company_name,
                "salary_min": vacancy.salary_min,
                "salary_max": vacancy.salary_max
            }
        }
        applications.append(app_data)
    
    return applications


@router.get("/{application_id}/resume")
async def download_resume(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Скачивание резюме из заявки
    """
    result = await db.execute(
        select(VacancyApplication, Vacancy)
        .join(Vacancy, VacancyApplication.vacancy_id == Vacancy.id)
        .where(VacancyApplication.id == application_id)
    )
    
    application, vacancy = result.first() or (None, None)
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заявка не найдена"
        )
    
    # Проверяем права доступа
    if not (current_user.id == application.candidate_id or 
            current_user.id == vacancy.creator_id or 
            current_user.is_hr):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав для скачивания этого резюме"
        )
    
    if not application.resume_file_path or not os.path.exists(application.resume_file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Файл резюме не найден"
        )
    
    return FileResponse(
        path=application.resume_file_path,
        filename=application.resume_file_name or "resume.pdf",
        media_type="application/pdf"
    )


@router.put("/{application_id}/status", response_model=VacancyApplicationRead)
async def update_application_status(
    application_id: int,
    status_update: ApplicationStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Обновление статуса заявки (только для HR)
    """
    if not current_user.is_hr:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только HR могут изменять статус заявок"
        )
    
    result = await db.execute(
        select(VacancyApplication, Vacancy)
        .join(Vacancy, VacancyApplication.vacancy_id == Vacancy.id)
        .where(VacancyApplication.id == application_id)
    )
    
    application, vacancy = result.first() or (None, None)
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заявка не найдена"
        )
    
    # Проверяем, что HR является создателем вакансии
    if current_user.id != vacancy.creator_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете изменять статус только заявок на свои вакансии"
        )
    
    # Валидация статуса
    valid_statuses = ["pending", "under_review", "accepted", "rejected", "interview_scheduled", "interview_completed"]
    if status_update.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый статус. Доступные: {', '.join(valid_statuses)}"
        )
    
    # Обновляем статус
    old_status = application.status
    application.status = status_update.status
    application.status_updated_at = datetime.utcnow()
    
    if status_update.notes:
        application.notes = status_update.notes
    
    await db.commit()
    await db.refresh(application)
    
    logger.info(f"Application {application_id} status changed from {old_status} to {status_update.status}")
    
    return application


@router.post("/{application_id}/schedule-interview", response_model=VacancyApplicationRead)
async def schedule_interview(
    application_id: int,
    interview_data: InterviewSchedule,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Назначение интервью (только для HR)
    """
    if not current_user.is_hr:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только HR могут назначать интервью"
        )
    
    result = await db.execute(
        select(VacancyApplication, Vacancy)
        .join(Vacancy, VacancyApplication.vacancy_id == Vacancy.id)
        .where(VacancyApplication.id == application_id)
    )
    
    application, vacancy = result.first() or (None, None)
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заявка не найдена"
        )
    
    # Проверяем, что HR является создателем вакансии
    if current_user.id != vacancy.creator_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете назначать интервью только для своих вакансий"
        )
    
    # Обновляем данные интервью
    application.interview_date = interview_data.interview_date
    application.interview_link = interview_data.interview_link
    application.interview_notes = interview_data.interview_notes
    application.status = "interview_scheduled"
    application.status_updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(application)
    
    logger.info(f"Interview scheduled for application {application_id}")
    
    return application


@router.post("/batch-analyze", response_model=dict)
async def batch_analyze_resumes(
    application_ids: list[int],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Пакетный анализ резюме (только для HR)
    Позволяет HR проанализировать несколько заявок одновременно для экономии времени
    """
    if not current_user.is_hr:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только HR могут выполнять пакетный анализ"
        )
    
    try:
        from app.services.resume_analysis_service import ResumeAnalysisService
        
        # Получаем заявки
        result = await db.execute(
            select(VacancyApplication).where(
                VacancyApplication.id.in_(application_ids)
            )
        )
        applications = result.scalars().all()
        
        if not applications:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Заявки не найдены"
            )
        
        # Выполняем пакетный анализ
        analysis_result = await ResumeAnalysisService.batch_analyze_applications(applications, db)
        
        return {
            "message": "Пакетный анализ завершен",
            "result": analysis_result
        }
        
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при пакетном анализе: {str(e)}"
        )
