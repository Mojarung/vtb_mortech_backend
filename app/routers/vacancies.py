from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.models import Vacancy, User, VacancyStatus
from app.schemas import VacancyCreate, VacancyUpdate, VacancyResponse
from app.auth import get_current_user, get_current_hr_user

router = APIRouter()

@router.post("/", response_model=VacancyResponse)
def create_vacancy(
    vacancy: VacancyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_hr_user)
):
    db_vacancy = Vacancy(**vacancy.dict(), creator_id=current_user.id)
    db.add(db_vacancy)
    db.commit()
    db.refresh(db_vacancy)
    return db_vacancy

@router.get("/", response_model=List[VacancyResponse])
def get_vacancies(
    skip: int = 0,
    limit: int = 100,
    status: VacancyStatus = None,
    db: Session = Depends(get_db)
):
    query = db.query(Vacancy).join(User)
    if status:
        query = query.filter(Vacancy.status == status)
    return query.offset(skip).limit(limit).all()

@router.get("/formatted")
def get_formatted_vacancies(
    skip: int = 0,
    limit: int = 100,
    status: VacancyStatus = None,
    db: Session = Depends(get_db)
):
    """Получение вакансий в формате, ожидаемом frontend"""
    try:
        query = db.query(Vacancy).join(User)
        if status:
            query = query.filter(Vacancy.status == status)
        
        vacancies = query.offset(skip).limit(limit).all()
        
        result = []
        for vacancy in vacancies:
            # Форматируем зарплату
            salary = "Не указана"
            if vacancy.salary_from and vacancy.salary_to:
                salary = f"{vacancy.salary_from:,} - {vacancy.salary_to:,} ₽".replace(',', ' ')
            elif vacancy.salary_from:
                salary = f"от {vacancy.salary_from:,} ₽".replace(',', ' ')
            elif vacancy.salary_to:
                salary = f"до {vacancy.salary_to:,} ₽".replace(',', ' ')
            
            # Форматируем требования
            requirements = []
            if vacancy.requirements:
                requirements = [req.strip() for req in vacancy.requirements.split(',') if req.strip()]
            
            result.append({
                "id": vacancy.id,
                "title": vacancy.title,
                "company": vacancy.creator.full_name or vacancy.creator.username,
                "location": vacancy.location or "Не указана",
                "salary": salary,
                "experience": vacancy.experience_level or "Не указан",
                "employment": vacancy.employment_type or "Полная занятость",
                "schedule": "Полный день",  # Можно добавить поле в модель
                "description": vacancy.description,
                "requirements": requirements,
                "benefits": ["ДМС", "Обучение", "Гибкий график"],  # Можно добавить поле в модель
                "rating": 4.5,  # Можно добавить поле в модель
                "applicants": 0,  # Можно подсчитать из заявок
                "postedDate": vacancy.created_at.strftime("%Y-%m-%d"),
                "deadline": (vacancy.created_at + timedelta(days=30)).strftime("%Y-%m-%d")  # Можно добавить поле в модель
            })
        
        return result
    except Exception as e:
        print(f"Error in get_formatted_vacancies: {e}")
        return []

@router.get("/open", response_model=List[VacancyResponse])
def get_open_vacancies(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return db.query(Vacancy).join(User).filter(
        Vacancy.status == VacancyStatus.OPEN
    ).offset(skip).limit(limit).all()

@router.get("/{vacancy_id}", response_model=VacancyResponse)
def get_vacancy(vacancy_id: int, db: Session = Depends(get_db)):
    vacancy = db.query(Vacancy).join(User).filter(Vacancy.id == vacancy_id).first()
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found"
        )
    return vacancy

@router.put("/{vacancy_id}", response_model=VacancyResponse)
def update_vacancy(
    vacancy_id: int,
    vacancy_update: VacancyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_hr_user)
):
    vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found"
        )
    
    if vacancy.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    update_data = vacancy_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vacancy, field, value)
    
    db.commit()
    db.refresh(vacancy)
    return vacancy

@router.delete("/{vacancy_id}")
def delete_vacancy(
    vacancy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_hr_user)
):
    vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found"
        )
    
    if vacancy.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    db.delete(vacancy)
    db.commit()
    return {"message": "Vacancy deleted successfully"}
