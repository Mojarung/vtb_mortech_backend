from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class PDFUploadRequest(BaseModel):
    """Схема для загрузки PDF файла"""
    filename: str = Field(..., description="Имя файла")
    file_size: int = Field(..., description="Размер файла в байтах")


class ExtractedText(BaseModel):
    """Схема для извлеченного текста"""
    page_number: int = Field(..., description="Номер страницы")
    text: str = Field(..., description="Извлеченный текст")
    confidence: float = Field(..., description="Уверенность OCR (0.0-1.0)")
    bounding_boxes: Optional[List[Dict[str, Any]]] = Field(None, description="Координаты блоков текста")


class ResumeData(BaseModel):
    """Схема для структурированных данных резюме"""
    name: Optional[str] = Field(None, description="Имя кандидата")
    email: Optional[str] = Field(None, description="Email")
    phone: Optional[str] = Field(None, description="Телефон")
    experience: Optional[str] = Field(None, description="Опыт работы")
    education: Optional[str] = Field(None, description="Образование")
    skills: List[str] = Field(default_factory=list, description="Навыки")
    languages: List[str] = Field(default_factory=list, description="Языки")
    summary: Optional[str] = Field(None, description="Краткое описание")
    raw_text: str = Field(..., description="Весь извлеченный текст")

    @field_validator('skills', 'languages', mode='before')
    @classmethod
    def coerce_list(cls, v):
        # Поддержка строк вида "Python, SQL" -> ["Python","SQL"]
        if v is None:
            return []
        if isinstance(v, list):
            return [str(i).strip() for i in v if str(i).strip()]
        if isinstance(v, str):
            return [s.strip() for s in v.split(',') if s.strip()]
        return []


class OCRResponse(BaseModel):
    """Схема ответа OCR сервиса"""
    success: bool = Field(..., description="Успешность операции")
    message: str = Field(..., description="Сообщение о результате")
    total_pages: int = Field(..., description="Общее количество страниц")
    extracted_text: List[ExtractedText] = Field(..., description="Извлеченный текст по страницам")
    resume_data: Optional[ResumeData] = Field(None, description="Структурированные данные резюме")
    processing_time: float = Field(..., description="Время обработки в секундах")
    file_info: Dict[str, Any] = Field(..., description="Информация о файле")


class OCRStatus(BaseModel):
    """Схема статуса OCR обработки"""
    status: str = Field(..., description="Статус обработки")
    progress: float = Field(..., description="Прогресс (0.0-1.0)")
    estimated_time: Optional[float] = Field(None, description="Оставшееся время в секундах")
    current_page: int = Field(..., description="Текущая обрабатываемая страница")
    total_pages: int = Field(..., description="Общее количество страниц")
