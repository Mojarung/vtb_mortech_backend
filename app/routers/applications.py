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
import httpx
import asyncio

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
    
    # Запускаем обработку OCR и нейронки в фоне
    asyncio.create_task(process_resume_with_ocr(db_resume.id, file_path, vacancy.description))
    
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
    print(f"🔄 Backend: Updating application {application_id} to status {new_status}")
    
    application = db.query(Resume).filter(Resume.id == application_id).first()
    
    if not application:
        print(f"❌ Backend: Application {application_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заявка не найдена"
        )
    
    try:
        status_enum = ApplicationStatus(new_status)
        print(f"✅ Backend: Status enum created: {status_enum}")
    except ValueError as e:
        print(f"❌ Backend: Invalid status {new_status}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный статус заявки"
        )
    
    application.status = status_enum
    application.updated_at = datetime.utcnow()
    
    if notes:
        application.notes = notes
    
    db.commit()
    print(f"✅ Backend: Application {application_id} status updated to {new_status}")
    
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

async def process_resume_with_ocr(resume_id: int, file_path: str, job_description: str):
    """Обработка резюме через OCR и нейронку"""
    try:
        print(f"🔄 Начинаем обработку резюме {resume_id}")
        
        # 1. Отправляем файл в OCR сервис
        ocr_text = await extract_text_with_ocr(file_path)
        if not ocr_text:
            print(f"❌ OCR не смог извлечь текст из файла {file_path}")
            return
        
        print(f"✅ OCR извлек текст: {len(ocr_text)} символов")
        
        # 2. Отправляем в нейронку для анализа
        ai_result = await analyze_resume_with_ai(ocr_text, job_description)
        if not ai_result:
            print(f"❌ Нейронка не смогла проанализировать резюме {resume_id}")
            return
        
        print(f"✅ Нейронка проанализировала резюме: получена рекомендация '{ai_result.get('recommendation')}'")
        
        # 3. Обновляем статус заявки и помечаем как обработанную
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            resume = db.query(Resume).filter(Resume.id == resume_id).first()
            if resume:
                resume.status = ApplicationStatus.PENDING
                resume.processed = True
                # Сохраняем полный текст анализа, плюс явную строку с рекомендацией
                resume.notes = f"{ai_result['text']}\n\nРЕКОМЕНДАЦИЯ_СТРУКТУРА: {ai_result.get('recommendation', '')}".strip()
                db.commit()
                print(f"✅ Заявка {resume_id} обновлена и готова для HR")
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Ошибка при обработке резюме {resume_id}: {e}")

async def extract_text_with_ocr(file_path: str) -> Optional[str]:
    """Извлечение текста из файла через OCR сервис"""
    try:
        ocr_url = "https://mojarung-vtb-mortech-ocr-1103.twc1.net/ocr/process-file"
        
        with open(file_path, "rb") as file:
            files = {"file": (os.path.basename(file_path), file, "application/octet-stream")}
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(ocr_url, files=files)
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("text", "")
                else:
                    print(f"❌ OCR сервис вернул ошибку: {response.status_code} - {response.text}")
                    return None
                    
    except Exception as e:
        print(f"❌ Ошибка при обращении к OCR сервису: {e}")
        return None

async def analyze_resume_with_ai(resume_text: str, job_description: str) -> Optional[dict]:
    """Анализ резюме через нейронку"""
    try:
        # Импортируем сервис анализа резюме
        from app.services.resume_analysis_service import get_resume_analysis_service
        
        # Получаем экземпляр сервиса
        service = get_resume_analysis_service()
        
        # Вызываем функцию анализа (параметры в правильном порядке)
        analysis_result = await service.analyze_resume(job_description, resume_text)
        
        if analysis_result and "basic_info" in analysis_result:
            # Формируем подробный текст анализа
            basic_info = analysis_result["basic_info"]
            detailed_analysis = analysis_result.get("detailed_analysis", {})
            
            analysis_text = f"""
🤖 АНАЛИЗ ИИ:

📊 ОСНОВНАЯ ИНФОРМАЦИЯ:
• Имя: {basic_info.get('name', 'Не указано')}
• Позиция: {basic_info.get('position', 'Не определена')}
• Опыт: {basic_info.get('experience', 'Не указан')}
• Образование: {basic_info.get('education', 'Не указано')}
• Соответствие: {basic_info.get('match_score', '0%')}

🎯 РЕКОМЕНДАЦИЯ: {basic_info.get('recommendation', 'Требует дополнительного анализа')}

📝 ПОДРОБНЫЙ АНАЛИЗ:
{detailed_analysis.get('analysis_text', 'Подробный анализ не проведен')}

✅ СИЛЬНЫЕ СТОРОНЫ:
{chr(10).join([f"• {strength}" for strength in detailed_analysis.get('strengths', [])])}

❌ СЛАБЫЕ СТОРОНЫ:
{chr(10).join([f"• {weakness}" for weakness in detailed_analysis.get('weaknesses', [])])}

🔧 ОТСУТСТВУЮЩИЕ НАВЫКИ:
{chr(10).join([f"• {skill}" for skill in detailed_analysis.get('missing_skills', [])])}


🛡️ ПРОВЕРКА НА МАНИПУЛЯЦИИ:
{analysis_result.get('anti_manipulation', {}).get('suspicious_phrases_found', False) and '⚠️ Обнаружены подозрительные фразы' or '✅ Резюме выглядит честно'}
"""
            return {
                "text": analysis_text.strip(),
                "recommendation": basic_info.get('recommendation', 'Требует дополнительного анализа')
            }
        else:
            return None
            
    except Exception as e:
        print(f"❌ Ошибка при анализе резюме нейронкой: {e}")
        return None
