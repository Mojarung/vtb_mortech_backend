from __future__ import annotations

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
    VacancyApplicationCreate,
    VacancyApplicationRead,
    VacancyApplicationUpdate
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/vacancies", tags=["vacancies"])


@router.post("/", response_model=VacancyRead, status_code=status.HTTP_201_CREATED)
async def create_vacancy(
    vacancy: VacancyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создать вакансию (только для HR)"""
    if not current_user.is_hr:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только HR могут создавать вакансии"
        )
    
    db_vacancy = Vacancy(
        **vacancy.dict(),
        hr_user_id=current_user.id
    )
    db.add(db_vacancy)
    await db.commit()
    await db.refresh(db_vacancy)
    return db_vacancy


@router.get("/", response_model=List[VacancyRead])
async def get_vacancies(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Получить список всех активных вакансий"""
    result = await db.execute(
        select(Vacancy)
        .where(Vacancy.is_active == True)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{vacancy_id}", response_model=VacancyRead)
async def get_vacancy(
    vacancy_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить вакансию по ID"""
    result = await db.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id)
    )
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
    """Обновить вакансию (только HR создатель)"""
    result = await db.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id)
    )
    db_vacancy = result.scalar_one_or_none()
    
    if not db_vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вакансия не найдена"
        )
    
    if db_vacancy.hr_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только создатель может редактировать вакансию"
        )
    
    for field, value in vacancy_update.dict(exclude_unset=True).items():
        setattr(db_vacancy, field, value)
    
    await db.commit()
    await db.refresh(db_vacancy)
    return db_vacancy


@router.delete("/{vacancy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vacancy(
    vacancy_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить вакансию (только HR создатель)"""
    result = await db.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id)
    )
    db_vacancy = result.scalar_one_or_none()
    
    if not db_vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вакансия не найдена"
        )
    
    if db_vacancy.hr_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только создатель может удалять вакансию"
        )
    
    await db.delete(db_vacancy)
    await db.commit()


@router.post("/{vacancy_id}/apply", response_model=VacancyApplicationRead)
async def apply_to_vacancy(
    vacancy_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Подать заявку на вакансию"""
    # Проверяем что вакансия существует и активна
    result = await db.execute(
        select(Vacancy).where(
            Vacancy.id == vacancy_id,
            Vacancy.is_active == True
        )
    )
    vacancy = result.scalar_one_or_none()
    
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вакансия не найдена или неактивна"
        )
    
    # Проверяем что пользователь не HR
    if current_user.is_hr:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="HR не могут подавать заявки на вакансии"
        )
    
    # Проверяем что заявка уже не подана
    existing_application = await db.execute(
        select(VacancyApplication).where(
            VacancyApplication.vacancy_id == vacancy_id,
            VacancyApplication.candidate_id == current_user.id
        )
    )
    
    if existing_application.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Заявка уже подана"
        )
    
    # Создаем заявку
    application = VacancyApplication(
        vacancy_id=vacancy_id,
        candidate_id=current_user.id
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)
    return application


@router.get("/{vacancy_id}/applications", response_model=List[VacancyApplicationRead])
async def get_vacancy_applications(
    vacancy_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить заявки на вакансию (только HR создатель)"""
    # Проверяем что вакансия существует
    result = await db.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id)
    )
    vacancy = result.scalar_one_or_none()
    
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вакансия не найдена"
        )
    
    # Проверяем права доступа
    if vacancy.hr_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только создатель может просматривать заявки"
        )
    
    result = await db.execute(
        select(VacancyApplication).where(
            VacancyApplication.vacancy_id == vacancy_id
        )
    )
    return result.scalars().all()


@router.put("/applications/{application_id}", response_model=VacancyApplicationRead)
async def update_application_status(
    application_id: int,
    application_update: VacancyApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновить статус заявки (только HR создатель вакансии)"""
    result = await db.execute(
        select(VacancyApplication).where(VacancyApplication.id == application_id)
    )
    application = result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заявка не найдена"
        )
    
    # Проверяем права доступа
    vacancy_result = await db.execute(
        select(Vacancy).where(Vacancy.id == application.vacancy_id)
    )
    vacancy = vacancy_result.scalar_one_or_none()
    
    if vacancy.hr_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только создатель вакансии может изменять статус заявки"
        )
    
    for field, value in application_update.dict(exclude_unset=True).items():
        setattr(application, field, value)
    
    await db.commit()
    await db.refresh(application)
    return application
