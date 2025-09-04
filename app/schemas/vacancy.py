from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class VacancyBase(BaseModel):
    title: str
    company_name: str
    rating: Optional[float] = None
    about: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    experience_years: Optional[int] = None
    requirements: Optional[str] = None
    conditions: Optional[str] = None


class VacancyCreate(VacancyBase):
    pass


class VacancyUpdate(BaseModel):
    title: Optional[str] = None
    company_name: Optional[str] = None
    rating: Optional[float] = None
    about: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    experience_years: Optional[int] = None
    requirements: Optional[str] = None
    conditions: Optional[str] = None
    is_active: Optional[bool] = None


class VacancyRead(VacancyBase):
    id: int
    creator_id: int
    location: Optional[str] = None
    created_at: datetime
    is_active: bool = True

    class Config:
        from_attributes = True


class VacancyApplicationBase(BaseModel):
    vacancy_id: int
    candidate_id: int
    status: str = "pending"
    cover_letter: Optional[str] = None
    notes: Optional[str] = None
    interview_date: Optional[datetime] = None
    interview_link: Optional[str] = None
    interview_notes: Optional[str] = None
    ai_recommendation: Optional[str] = None
    ai_match_percentage: Optional[int] = None
    ai_analysis_date: Optional[datetime] = None


class VacancyApplicationCreate(VacancyApplicationBase):
    pass


class VacancyApplicationUpdate(BaseModel):
    status: Optional[str] = None
    cover_letter: Optional[str] = None
    notes: Optional[str] = None
    interview_date: Optional[datetime] = None
    interview_link: Optional[str] = None
    interview_notes: Optional[str] = None


class VacancyApplicationRead(VacancyApplicationBase):
    id: int
    resume_file_path: Optional[str] = None
    resume_file_name: Optional[str] = None
    resume_file_size: Optional[int] = None
    applied_at: datetime
    status_updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApplicationStatusUpdate(BaseModel):
    """Схема для обновления статуса заявки"""
    status: str
    notes: Optional[str] = None


class InterviewSchedule(BaseModel):
    """Схема для назначения интервью"""
    interview_date: datetime
    interview_link: str
    interview_notes: Optional[str] = None


class VacancyApplicationWithDetails(VacancyApplicationRead):
    """Расширенная схема с деталями кандидата и вакансии"""
    candidate: Optional[dict] = None  # Будет заполнено в API
    vacancy: Optional[dict] = None    # Будет заполнено в API
