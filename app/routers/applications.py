from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import User, Vacancy, Resume, ApplicationStatus
from app.auth import get_current_user, get_current_hr_user
from app.schemas import ResumeResponse
from datetime import datetime
import os
import shutil

router = APIRouter()

@router.post("/apply/{vacancy_id}", response_model=ResumeResponse)
async def apply_for_vacancy(
    vacancy_id: int,
    file: UploadFile = File(...),
    cover_letter: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Подача заявки на вакансию"""
    
    # Проверяем, что вакансия существует и открыта
    vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вакансия не найдена"
        )
    
    if vacancy.status.value != "open":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вакансия закрыта для подачи заявок"
        )
    
    # Проверяем, что пользователь еще не подавал заявку на эту вакансию
    existing_application = db.query(Resume).filter(
        Resume.user_id == current_user.id,
        Resume.vacancy_id == vacancy_id
    ).first()
    
    if existing_application:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вы уже подавали заявку на эту вакансию"
        )
    
    # Создаем директорию для файлов, если её нет
    upload_dir = "uploads/resumes"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Генерируем уникальное имя файла
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{current_user.id}_{vacancy_id}_{timestamp}_{file.filename}"
    file_path = os.path.join(upload_dir, filename)
    
    # Сохраняем файл
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при сохранении файла: {str(e)}"
        )
    
    # Создаем запись в базе данных
    db_resume = Resume(
        user_id=current_user.id,
        vacancy_id=vacancy_id,
        file_path=file_path,
        original_filename=file.filename,
        status=ApplicationStatus.PENDING,
        notes=cover_letter
    )
    
    db.add(db_resume)
    db.commit()
    db.refresh(db_resume)
    
    return db_resume

@router.get("/my-applications", response_model=List[ResumeResponse])
def get_my_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение заявок текущего пользователя"""
    return db.query(Resume).join(Vacancy).filter(
        Resume.user_id == current_user.id
    ).order_by(Resume.uploaded_at.desc()).all()

@router.get("/all", response_model=List[ResumeResponse])
def get_all_applications(
    status_filter: Optional[str] = None,
    vacancy_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_hr_user)
):
    """Получение всех заявок для HR"""
    query = db.query(Resume).join(User).join(Vacancy)
    
    if status_filter:
        try:
            status_enum = ApplicationStatus(status_filter)
            query = query.filter(Resume.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный статус заявки"
            )
    
    if vacancy_id:
        query = query.filter(Resume.vacancy_id == vacancy_id)
    
    return query.order_by(Resume.uploaded_at.desc()).all()

@router.get("/{application_id}", response_model=ResumeResponse)
def get_application_details(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение деталей заявки"""
    application = db.query(Resume).filter(Resume.id == application_id).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заявка не найдена"
        )
    
    # Проверяем права доступа
    if current_user.role.value == "user" and application.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этой заявке"
        )
    
    return application

@router.put("/{application_id}/status")
def update_application_status(
    application_id: int,
    new_status: str,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_hr_user)
):
    """Обновление статуса заявки (только для HR)"""
    application = db.query(Resume).filter(Resume.id == application_id).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заявка не найдена"
        )
    
    try:
        status_enum = ApplicationStatus(new_status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный статус заявки"
        )
    
    application.status = status_enum
    application.updated_at = datetime.utcnow()
    
    if notes:
        application.notes = notes
    
    db.commit()
    
    return {"message": "Статус заявки обновлен", "new_status": new_status}

@router.delete("/{application_id}")
def delete_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удаление заявки"""
    application = db.query(Resume).filter(Resume.id == application_id).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заявка не найдена"
        )
    
    # Проверяем права доступа
    if current_user.role.value == "user" and application.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этой заявке"
        )
    
    # Удаляем файл
    try:
        if os.path.exists(application.file_path):
            os.remove(application.file_path)
    except Exception as e:
        print(f"Ошибка при удалении файла: {e}")
    
    db.delete(application)
    db.commit()
    
    return {"message": "Заявка удалена"}

@router.get("/stats/summary")
def get_application_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_hr_user)
):
    """Получение статистики заявок для HR"""
    total_applications = db.query(Resume).count()
    pending_applications = db.query(Resume).filter(
        Resume.status == ApplicationStatus.PENDING
    ).count()
    reviewed_applications = db.query(Resume).filter(
        Resume.status == ApplicationStatus.REVIEWED
    ).count()
    accepted_applications = db.query(Resume).filter(
        Resume.status == ApplicationStatus.ACCEPTED
    ).count()
    rejected_applications = db.query(Resume).filter(
        Resume.status == ApplicationStatus.REJECTED
    ).count()
    
    return {
        "total": total_applications,
        "pending": pending_applications,
        "reviewed": reviewed_applications,
        "accepted": accepted_applications,
        "rejected": rejected_applications
    }
