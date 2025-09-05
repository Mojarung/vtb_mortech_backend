"""
Роутер для анализа резюме
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import ResumeAnalyzeRequest, ResumeAnalyzeResponse
from app.services.resume_analysis_service import get_resume_analysis_service
from app.auth import get_current_user
from app.models import User

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "Resume Analyzer API is running"}

@router.post("/analyze_resume", response_model=ResumeAnalyzeResponse)
async def analyze_resume(
    request: ResumeAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Анализирует резюме относительно вакансии
    """
    
    # Проверяем входные данные
    if not request.job_description.strip():
        raise HTTPException(status_code=400, detail="job_description не может быть пустым")
    
    if not request.resume_text.strip():
        raise HTTPException(status_code=400, detail="resume_text не может быть пустым")
    
    try:
        # Анализируем резюме
        service = get_resume_analysis_service()
        analysis_result = await service.analyze_resume(
            request.job_description, 
            request.resume_text
        )
        
        return ResumeAnalyzeResponse(**analysis_result)
        
    except Exception as e:
        import traceback
        print(f"Ошибка в analyze_resume: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Ошибка анализа резюме: {str(e)}")
