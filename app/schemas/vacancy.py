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
    hr_user_id: int
    published_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class VacancyApplicationBase(BaseModel):
    vacancy_id: int
    candidate_id: int
    status: str = "pending"


class VacancyApplicationCreate(VacancyApplicationBase):
    pass


class VacancyApplicationUpdate(BaseModel):
    status: Optional[str] = None


class VacancyApplicationRead(VacancyApplicationBase):
    id: int
    applied_at: datetime

    class Config:
        from_attributes = True
