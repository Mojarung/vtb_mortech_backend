from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database import get_db
from app.models import User, Vacancy, Resume, Interview, ResumeAnalysis, InterviewStatus, UserRole
from app.auth import get_current_user, get_current_hr_user
from app.schemas import UserResponse
from typing import Dict, Any

router = APIRouter()

@router.get("/debug/stats")
def debug_stats(db: Session = Depends(get_db)):
    """Debug endpoint для проверки данных в базе"""
    try:
        user_count = db.query(User).count()
        vacancy_count = db.query(Vacancy).count()
        resume_count = db.query(Resume).count()
        interview_count = db.query(Interview).count()
        
        return {
            "users": user_count,
            "vacancies": vacancy_count,
            "resumes": resume_count,
            "interviews": interview_count
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/candidate/stats")
def get_candidate_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение статистики для кандидата"""
    
    try:
        # Общее количество интервью
        total_interviews = db.query(Interview).join(Resume).filter(
            Resume.user_id == current_user.id
        ).count()
        
        # Завершенные интервью
        completed_interviews = db.query(Interview).join(Resume).filter(
            Resume.user_id == current_user.id,
            Interview.status == InterviewStatus.COMPLETED
        ).count()
        
        # Запланированные интервью
        scheduled_interviews = db.query(Interview).join(Resume).filter(
            Resume.user_id == current_user.id,
            Interview.status == InterviewStatus.NOT_STARTED
        ).count()
        
        # Средний балл по завершенным интервью
        avg_score = db.query(func.avg(Interview.pass_percentage)).join(Resume).filter(
            Resume.user_id == current_user.id,
            Interview.status == InterviewStatus.COMPLETED,
            Interview.pass_percentage.isnot(None)
        ).scalar() or 0
        
        return {
            "total_interviews": total_interviews,
            "completed_interviews": completed_interviews,
            "scheduled_interviews": scheduled_interviews,
            "average_score": round(avg_score, 1) if avg_score else 0
        }
    except Exception as e:
        print(f"Error in get_candidate_stats: {e}")
        # Возвращаем нулевые значения в случае ошибки
        return {
            "total_interviews": 0,
            "completed_interviews": 0,
            "scheduled_interviews": 0,
            "average_score": 0
        }

@router.get("/hr/stats")
def get_hr_stats(
    current_user: User = Depends(get_current_hr_user),
    db: Session = Depends(get_db)
):
    """Получение статистики для HR"""
    
    try:
        # Общее количество кандидатов (уникальные пользователи с резюме)
        total_candidates = db.query(func.count(func.distinct(Resume.user_id))).filter(
            Resume.user_id.isnot(None)
        ).scalar() or 0
        
        # Общее количество интервью
        total_interviews = db.query(Interview).count()
        
        # Успешные наймы (интервью с высоким процентом прохождения)
        successful_hires = db.query(Interview).filter(
            Interview.pass_percentage >= 80,
            Interview.status == InterviewStatus.COMPLETED
        ).count()
        
        # Ожидающие интервью
        pending_interviews = db.query(Interview).filter(
            Interview.status == InterviewStatus.NOT_STARTED
        ).count()
        
        # Количество вакансий от текущего HR
        hr_vacancies = db.query(Vacancy).filter(
            Vacancy.creator_id == current_user.id
        ).count()
        
        return {
            "total_candidates": total_candidates,
            "total_interviews": total_interviews,
            "successful_hires": successful_hires,
            "pending_interviews": pending_interviews,
            "hr_vacancies": hr_vacancies
        }
    except Exception as e:
        print(f"Error in get_hr_stats: {e}")
        # Возвращаем нулевые значения в случае ошибки
        return {
            "total_candidates": 0,
            "total_interviews": 0,
            "successful_hires": 0,
            "pending_interviews": 0,
            "hr_vacancies": 0
        }

@router.get("/candidate/recent-interviews")
def get_candidate_recent_interviews(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение последних интервью кандидата"""
    
    try:
        interviews = db.query(Interview).join(Resume).join(Vacancy).filter(
            Resume.user_id == current_user.id
        ).order_by(desc(Interview.created_at)).limit(10).all()
        
        result = []
        for interview in interviews:
            result.append({
                "id": interview.id,
                "company": interview.vacancy.title if interview.vacancy else "Неизвестная компания",
                "position": interview.vacancy.title if interview.vacancy else "Неизвестная позиция",
                "date": interview.scheduled_date.isoformat() if interview.scheduled_date else None,
                "status": interview.status.value,
                "score": interview.pass_percentage,
                "feedback": interview.summary
            })
        
        return result
    except Exception as e:
        return []

@router.get("/hr/recent-interviews")
def get_hr_recent_interviews(
    current_user: User = Depends(get_current_hr_user),
    db: Session = Depends(get_db)
):
    """Получение последних интервью для HR"""
    
    try:
        interviews = db.query(Interview).join(Vacancy).filter(
            Vacancy.creator_id == current_user.id
        ).order_by(desc(Interview.created_at)).limit(10).all()
        
        result = []
        for interview in interviews:
            candidate_name = "Неизвестный кандидат"
            if interview.resume and interview.resume.user:
                candidate_name = interview.resume.user.full_name or interview.resume.user.username
            
            result.append({
                "id": interview.id,
                "candidate": candidate_name,
                "position": interview.vacancy.title if interview.vacancy else "Неизвестная позиция",
                "date": interview.scheduled_date.isoformat() if interview.scheduled_date else None,
                "score": interview.pass_percentage,
                "status": interview.status.value
            })
        
        return result
    except Exception as e:
        return []

@router.get("/candidates")
def get_candidates(
    current_user: User = Depends(get_current_hr_user),
    db: Session = Depends(get_db)
):
    """Получение списка кандидатов для HR"""
    
    try:
        # Получаем всех пользователей с ролью 'user' (кандидаты)
        candidates = db.query(User).filter(User.role == UserRole.USER).all()
        
        result = []
        for candidate in candidates:
            # Получаем последнее резюме кандидата
            last_resume = db.query(Resume).filter(
                Resume.user_id == candidate.id
            ).order_by(desc(Resume.uploaded_at)).first()
            
            # Получаем последнее интервью
            last_interview = None
            if last_resume:
                last_interview = db.query(Interview).filter(
                    Interview.resume_id == last_resume.id
                ).order_by(desc(Interview.created_at)).first()
            
            result.append({
                "id": str(candidate.id).zfill(5),  # Форматируем ID как в mock данных
                "name": candidate.full_name or candidate.username,
                "position": last_resume.vacancy.title if last_resume and last_resume.vacancy else "Не указана",
                "address": candidate.location or "Не указан",
                "date": last_resume.uploaded_at.strftime("%d %b %Y") if last_resume else candidate.created_at.strftime("%d %b %Y"),
                "type": "Техническое",  # Можно добавить логику определения типа
                "status": last_interview.status.value if last_interview else "Новое",
                "statusColor": get_status_color(last_interview.status if last_interview else None)
            })
        
        return result
    except Exception as e:
        print(f"Error in get_candidates: {e}")
        return []

def get_status_color(status):
    """Получение цвета статуса"""
    if not status:
        return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
    
    status_colors = {
        InterviewStatus.COMPLETED: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
        InterviewStatus.IN_PROGRESS: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
        InterviewStatus.NOT_STARTED: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
    }
    
    return status_colors.get(status, "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200")