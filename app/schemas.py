from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models import UserRole, VacancyStatus, InterviewStatus

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole
    full_name: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class VacancyCreate(BaseModel):
    title: str
    description: str
    requirements: Optional[str] = None
    salary_from: Optional[int] = None
    salary_to: Optional[int] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    status: VacancyStatus = VacancyStatus.OPEN
    original_url: Optional[str] = None

class VacancyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    salary_from: Optional[int] = None
    salary_to: Optional[int] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    status: Optional[VacancyStatus] = None
    original_url: Optional[str] = None

class VacancyResponse(BaseModel):
    id: int
    title: str
    description: str
    requirements: Optional[str]
    salary_from: Optional[int]
    salary_to: Optional[int]
    location: Optional[str]
    employment_type: Optional[str]
    experience_level: Optional[str]
    status: VacancyStatus
    original_url: Optional[str]
    creator_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ResumeResponse(BaseModel):
    id: int
    user_id: Optional[int]
    vacancy_id: int
    file_path: str
    original_filename: str
    uploaded_at: datetime
    processed: bool
    uploaded_by_hr: bool

    class Config:
        from_attributes = True

class ResumeAnalysisResponse(BaseModel):
    id: int
    resume_id: int
    name: Optional[str]
    position: Optional[str]
    experience: Optional[str]
    education: Optional[str]
    upload_date: Optional[str]
    match_score: Optional[str]
    key_skills: Optional[List[str]]
    recommendation: Optional[str]
    projects: Optional[List[str]]
    work_experience: Optional[List[str]]
    technologies: Optional[List[str]]
    achievements: Optional[List[str]]
    structured: Optional[bool]
    effort_level: Optional[str]
    suspicious_phrases_found: Optional[bool]
    suspicious_examples: Optional[List[str]]
    created_at: datetime

    class Config:
        from_attributes = True

class InterviewCreate(BaseModel):
    vacancy_id: int
    resume_id: int
    scheduled_date: datetime
    notes: Optional[str] = None

class InterviewUpdate(BaseModel):
    status: Optional[InterviewStatus] = None
    scheduled_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    dialogue: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    pass_percentage: Optional[float] = None
    notes: Optional[str] = None

class InterviewResponse(BaseModel):
    id: int
    vacancy_id: int
    resume_id: int
    status: InterviewStatus
    scheduled_date: Optional[datetime]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    duration_minutes: Optional[int]
    dialogue: Optional[Dict[str, Any]]
    summary: Optional[str]
    pass_percentage: Optional[float]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Resume Analysis Schemas (from resume_analysis)
class ResumeAnalyzeRequest(BaseModel):
    job_description: str
    resume_text: str

class BasicInfo(BaseModel):
    name: Optional[str] = None
    position: Optional[str] = None
    experience: Optional[str] = None
    education: Optional[str] = None
    upload_date: str
    match_score: str
    key_skills: List[str]
    recommendation: str

class ExtendedInfo(BaseModel):
    projects: List[str]
    work_experience: List[str]
    technologies: List[str]
    achievements: List[str]

class ResumeQuality(BaseModel):
    structured: bool
    effort_level: str

class AntiManipulation(BaseModel):
    suspicious_phrases_found: bool
    examples: List[str]

class ResumeAnalyzeResponse(BaseModel):
    basic_info: BasicInfo
    extended_info: ExtendedInfo
    resume_quality: ResumeQuality
    anti_manipulation: AntiManipulation