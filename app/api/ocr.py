from __future__ import annotations

import time
from typing import List
from fastapi import APIRouter, File, UploadFile, HTTPException, status, Depends
from fastapi.responses import JSONResponse

from app.schemas.ocr import OCRResponse, OCRStatus, ExtractedText, ResumeData
from app.services.ocr_service import OCRService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/ocr", tags=["ocr"])


@router.post("/process-pdf", response_model=OCRResponse)
async def process_pdf(
    file: UploadFile = File(..., description="PDF файл для обработки"),
    current_user: User = Depends(get_current_user)
):
    """
    Обработка PDF резюме с помощью OCR
    
    - **file**: PDF файл для обработки
    - **current_user**: Текущий авторизованный пользователь
    
    Возвращает:
    - Извлеченный текст по страницам
    - Структурированные данные резюме
    - Статистику обработки
    """
    
    # Проверяем тип файла
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поддерживаются только PDF файлы"
        )
    
    # Проверяем размер файла (максимум 50MB)
    if file.size and file.size > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Размер файла не должен превышать 50MB"
        )
    
    try:
        start_time = time.time()
        
        # Читаем содержимое файла
        pdf_content = await file.read()
        
        if not pdf_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Файл пустой или поврежден"
            )
        
        print(f"📁 Обрабатываю файл: {file.filename} ({len(pdf_content)} байт)")
        
        # Создаем OCR сервис
        ocr_service = OCRService()
        
        # Обрабатываем PDF
        extracted_text, resume_data = await ocr_service.process_pdf(pdf_content, file.filename)
        
        # Вычисляем время обработки
        processing_time = time.time() - start_time
        
        # Формируем ответ
        response = OCRResponse(
            success=True,
            message=f"PDF успешно обработан за {processing_time:.2f} секунд",
            total_pages=len(extracted_text),
            extracted_text=extracted_text,
            resume_data=resume_data,
            processing_time=processing_time,
            file_info={
                "filename": file.filename,
                "file_size": len(pdf_content),
                "content_type": file.content_type,
                "user_id": current_user.id,
                "username": current_user.username
            }
        )
        
        print(f"✅ OCR обработка завершена успешно")
        print(f"   Страниц: {len(extracted_text)}")
        print(f"   Время: {processing_time:.2f}с")
        print(f"   Пользователь: {current_user.username}")
        
        return response
        
    except Exception as e:
        print(f"❌ Ошибка OCR обработки: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка обработки PDF: {str(e)}"
        )


@router.post("/process-pdf-batch", response_model=List[OCRResponse])
async def process_pdf_batch(
    files: List[UploadFile] = File(..., description="Список PDF файлов для обработки"),
    current_user: User = Depends(get_current_user)
):
    """
    Пакетная обработка нескольких PDF резюме
    
    - **files**: Список PDF файлов для обработки
    - **current_user**: Текущий авторизованный пользователь
    
    Возвращает список результатов обработки для каждого файла
    """
    
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо загрузить хотя бы один файл"
        )
    
    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Максимальное количество файлов: 10"
        )
    
    results = []
    
    try:
        print(f"📦 Начинаю пакетную обработку {len(files)} файлов")
        
        for i, file in enumerate(files, 1):
            print(f"\n📁 Обрабатываю файл {i}/{len(files)}: {file.filename}")
            
            try:
                # Проверяем тип файла
                if not file.filename.lower().endswith('.pdf'):
                    results.append(OCRResponse(
                        success=False,
                        message=f"Файл {file.filename} не является PDF",
                        total_pages=0,
                        extracted_text=[],
                        resume_data=None,
                        processing_time=0.0,
                        file_info={
                            "filename": file.filename,
                            "file_size": file.size or 0,
                            "content_type": file.content_type,
                            "user_id": current_user.id,
                            "username": current_user.username,
                            "error": "Неверный тип файла"
                        }
                    ))
                    continue
                
                # Проверяем размер файла
                if file.size and file.size > 50 * 1024 * 1024:
                    results.append(OCRResponse(
                        success=False,
                        message=f"Файл {file.filename} слишком большой (>50MB)",
                        total_pages=0,
                        extracted_text=[],
                        resume_data=None,
                        processing_time=0.0,
                        file_info={
                            "filename": file.filename,
                            "file_size": file.size,
                            "content_type": file.content_type,
                            "user_id": current_user.id,
                            "username": current_user.username,
                            "error": "Превышен размер файла"
                        }
                    ))
                    continue
                
                # Обрабатываем файл
                start_time = time.time()
                pdf_content = await file.read()
                
                if not pdf_content:
                    results.append(OCRResponse(
                        success=False,
                        message=f"Файл {file.filename} пустой или поврежден",
                        total_pages=0,
                        extracted_text=[],
                        resume_data=None,
                        processing_time=0.0,
                        file_info={
                            "filename": file.filename,
                            "file_size": len(pdf_content),
                            "content_type": file.content_type,
                            "user_id": current_user.id,
                            "username": current_user.username,
                            "error": "Файл пустой"
                        }
                    ))
                    continue
                
                # OCR обработка
                ocr_service = OCRService()
                extracted_text, resume_data = await ocr_service.process_pdf(pdf_content, file.filename)
                
                processing_time = time.time() - start_time
                
                # Успешный результат
                results.append(OCRResponse(
                    success=True,
                    message=f"Файл {file.filename} успешно обработан",
                    total_pages=len(extracted_text),
                    extracted_text=extracted_text,
                    resume_data=resume_data,
                    processing_time=processing_time,
                    file_info={
                        "filename": file.filename,
                        "file_size": len(pdf_content),
                        "content_type": file.content_type,
                        "user_id": current_user.id,
                        "username": current_user.username
                    }
                ))
                
                print(f"   ✅ Успешно обработан за {processing_time:.2f}с")
                
            except Exception as e:
                print(f"   ❌ Ошибка обработки {file.filename}: {e}")
                
                # Результат с ошибкой
                results.append(OCRResponse(
                    success=False,
                    message=f"Ошибка обработки файла {file.filename}",
                    total_pages=0,
                    extracted_text=[],
                    resume_data=None,
                    processing_time=0.0,
                    file_info={
                        "filename": file.filename,
                        "file_size": file.size or 0,
                        "content_type": file.content_type,
                        "user_id": current_user.id,
                        "username": current_user.username,
                        "error": str(e)
                    }
                ))
        
        print(f"\n📊 Пакетная обработка завершена")
        print(f"   Успешно: {len([r for r in results if r.success])}")
        print(f"   С ошибками: {len([r for r in results if not r.success])}")
        
        return results
        
    except Exception as e:
        print(f"❌ Критическая ошибка пакетной обработки: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка пакетной обработки: {str(e)}"
        )


@router.get("/status/{task_id}", response_model=OCRStatus)
async def get_ocr_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Получение статуса OCR задачи (для асинхронной обработки)
    
    - **task_id**: ID задачи OCR
    - **current_user**: Текущий авторизованный пользователь
    """
    
    # TODO: Реализовать систему очередей для асинхронной обработки
    # Пока возвращаем заглушку
    
    return OCRStatus(
        status="completed",
        progress=1.0,
        estimated_time=0.0,
        current_page=1,
        total_pages=1
    )


@router.get("/health")
async def ocr_health_check():
    """
    Проверка состояния OCR сервиса
    """
    
    try:
        # Проверяем доступность Tesseract
        import pytesseract
        pytesseract.get_tesseract_version()
        
        return {
            "status": "healthy",
            "service": "OCR",
            "tesseract": "available",
            "message": "OCR сервис работает корректно"
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "service": "OCR",
                "error": str(e),
                "message": "OCR сервис недоступен"
            }
        )
