"""
API роутер для управления вакансиями
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import User, Vacancy, VacancyApplication
from app.schemas.vacancy import (
    VacancyCreate,
    VacancyRead,
    VacancyUpdate,
    VacancyApplicationWithDetails
)
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vacancies", tags=["vacancies"])


@router.post("/", response_model=VacancyRead, status_code=status.HTTP_201_CREATED)
async def create_vacancy(
    vacancy: VacancyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Создание новой вакансии (только для HR)
    """
    if not current_user.is_hr:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только HR могут создавать вакансии"
        )
    
    # Создаем вакансию
    db_vacancy = Vacancy(
        title=vacancy.title,
        company_name=vacancy.company_name,
        location=vacancy.location,
        salary_min=vacancy.salary_min,
        salary_max=vacancy.salary_max,
        experience_years=vacancy.experience_years,
        requirements=vacancy.requirements,
        conditions=vacancy.conditions,
        about=vacancy.about,
        creator_id=current_user.id
    )
    
    db.add(db_vacancy)
    await db.commit()
    await db.refresh(db_vacancy)
    
    logger.info(f"Vacancy created: {db_vacancy.title} by {current_user.username}")
    
    return db_vacancy


@router.get("/", response_model=List[VacancyRead])
async def get_vacancies(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Получение списка всех вакансий
    """
    result = await db.execute(
        select(Vacancy)
        .offset(skip)
        .limit(limit)
        .order_by(Vacancy.created_at.desc())
    )
    
    vacancies = result.scalars().all()
    return vacancies


@router.get("/{vacancy_id}", response_model=VacancyRead)
async def get_vacancy(
    vacancy_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Получение конкретной вакансии
    """
    result = await db.execute(select(Vacancy).where(Vacancy.id == vacancy_id))
    vacancy = result.scalar_one_or_none()
    
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вакансия не найдена"
        )
    
    return vacancy


@router.put("/{vacancy_id}", response_model=VacancyRead)
async def update_vacancy(
    vacancy_id: int,
    vacancy_update: VacancyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Обновление вакансии (только создатель)
    """
    result = await db.execute(select(Vacancy).where(Vacancy.id == vacancy_id))
    vacancy = result.scalar_one_or_none()
    
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вакансия не найдена"
        )
    
    # Проверяем права доступа
    if current_user.id != vacancy.creator_id and not current_user.is_hr:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете редактировать только свои вакансии"
        )
    
    # Обновляем поля
    update_data = vacancy_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vacancy, field, value)
    
    await db.commit()
    await db.refresh(vacancy)
    
    logger.info(f"Vacancy {vacancy_id} updated by {current_user.username}")
    
    return vacancy


@router.delete("/{vacancy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vacancy(
    vacancy_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Удаление вакансии (только создатель)
    """
    result = await db.execute(select(Vacancy).where(Vacancy.id == vacancy_id))
    vacancy = result.scalar_one_or_none()
    
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вакансия не найдена"
        )
    
    # Проверяем права доступа
    if current_user.id != vacancy.creator_id and not current_user.is_hr:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете удалять только свои вакансии"
        )
    
    await db.delete(vacancy)
    await db.commit()
    
    logger.info(f"Vacancy {vacancy_id} deleted by {current_user.username}")


@router.get("/{vacancy_id}/applications", response_model=List[VacancyApplicationWithDetails])
async def get_vacancy_applications(
    vacancy_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение заявок на вакансию (только создатель вакансии)
    """
    # Проверяем существование вакансии
    result = await db.execute(select(Vacancy).where(Vacancy.id == vacancy_id))
    vacancy = result.scalar_one_or_none()
    
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вакансия не найдена"
        )
    
    # Проверяем права доступа
    if current_user.id != vacancy.creator_id and not current_user.is_hr:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете просматривать заявки только на свои вакансии"
        )
    
    # Получаем заявки с информацией о кандидатах
    result = await db.execute(
        select(VacancyApplication, User)
        .join(User, VacancyApplication.candidate_id == User.id)
        .where(VacancyApplication.vacancy_id == vacancy_id)
        .order_by(VacancyApplication.applied_at.desc())
    )
    
    applications = []
    for application, candidate in result:
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
            "candidate": {
                "id": candidate.id,
                "username": candidate.username,
                "email": candidate.email,
                "skills": candidate.skills,
                "education": candidate.education,
                "experience_years": candidate.experience_years
            },
            "vacancy": {
                "id": vacancy.id,
                "title": vacancy.title,
                "company_name": vacancy.company_name
            }
        }
        applications.append(app_data)
    
    return applications


@router.get("/my/created", response_model=List[VacancyRead])
async def get_my_vacancies(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение вакансий, созданных текущим пользователем
    """
    if not current_user.is_hr:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только HR могут создавать вакансии"
        )
    
    result = await db.execute(
        select(Vacancy)
        .where(Vacancy.creator_id == current_user.id)
        .order_by(Vacancy.created_at.desc())
    )
    
    vacancies = result.scalars().all()
    return vacancies