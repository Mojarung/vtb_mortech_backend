from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, Float, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Vacancy(Base):
    __tablename__ = "vacancies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Основная информация
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Детали
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    about: Mapped[str | None] = mapped_column(Text, nullable=True)
    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    experience_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Требования и условия
    requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Метаданные
    published_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Связи
    hr_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    hr_user: Mapped["User"] = relationship("User", back_populates="vacancies")
    
    # Связь с кандидатами (many-to-many)
    candidates: Mapped[list["User"]] = relationship(
        "User", 
        secondary="vacancy_applications",
        back_populates="applied_vacancies"
    )


# Таблица для связи вакансий и кандидатов (many-to-many)
class VacancyApplication(Base):
    __tablename__ = "vacancy_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vacancy_id: Mapped[int] = mapped_column(Integer, ForeignKey("vacancies.id"), nullable=False)
    candidate_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Статусы: pending, under_review, accepted, rejected, interview_scheduled, interview_completed
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    
    # Резюме (PDF файл)
    resume_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Путь к PDF файлу
    resume_file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Оригинальное имя файла
    resume_file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Размер файла в байтах
    
    # Дополнительная информация
    cover_letter: Mapped[str | None] = mapped_column(Text, nullable=True)  # Сопроводительное письмо
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)  # Заметки HR
    
    # AI анализ резюме
    ai_recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)  # Рекомендация от ИИ
    ai_match_percentage: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Процент соответствия (0-100)
    ai_analysis_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # Дата анализа ИИ
    
    # Интервью
    interview_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    interview_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    interview_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Временные метки
    applied_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    status_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
