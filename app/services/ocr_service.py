from __future__ import annotations

import time
import re
import io
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

import PyPDF2
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image
import cv2
import numpy as np

from app.schemas.ocr import ExtractedText, ResumeData


class OCRService:
    """Сервис для OCR обработки PDF резюме"""
    
    def __init__(self):
        # Настройки Tesseract
        self.tesseract_config = '--oem 3 --psm 6'
        
        # Регулярные выражения для извлечения данных
        self.patterns = {
            'name': [
                r'^([А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?)',
                r'ФИО[:\s]+([А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+)',
                r'Имя[:\s]+([А-ЯЁ][а-яё]+)',
            ],
            'email': [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            ],
            'phone': [
                r'\+?[78][-\(]?\d{3}[-\)]?\d{3}[-]?\d{2}[-]?\d{2}',
                r'\b\d{3}[-]?\d{3}[-]?\d{2}[-]?\d{2}\b',
            ],
            'experience': [
                r'Опыт работы[:\s]+(.+?)(?=\n\n|\n[A-ZА-Я]|$)',
                r'Стаж[:\s]+(.+?)(?=\n\n|\n[A-ZА-Я]|$)',
                r'Работал[:\s]+(.+?)(?=\n\n|\n[A-ZА-Я]|$)',
            ],
            'education': [
                r'Образование[:\s]+(.+?)(?=\n\n|\n[A-ZА-Я]|$)',
                r'Университет[:\s]+(.+?)(?=\n\n|\n[A-ZА-Я]|$)',
                r'Институт[:\s]+(.+?)(?=\n\n|\n[A-ZА-Я]|$)',
            ],
            'skills': [
                r'Навыки[:\s]+(.+?)(?=\n\n|\n[A-ZА-Я]|$)',
                r'Технологии[:\s]+(.+?)(?=\n\n|\n[A-ZА-Я]|$)',
                r'Знаю[:\s]+(.+?)(?=\n\n|\n[A-ZА-Я]|$)',
            ],
            'languages': [
                r'Языки[:\s]+(.+?)(?=\n\n|\n[A-ZА-Я]|$)',
                r'Английский[:\s]+(.+?)(?=\n\n|\n[A-ZА-Я]|$)',
                r'Иностранные языки[:\s]+(.+?)(?=\n\n|\n[A-ZА-Я]|$)',
            ],
        }
    
    async def process_pdf(self, pdf_bytes: bytes, filename: str) -> Tuple[List[ExtractedText], ResumeData]:
        """Основной метод обработки PDF"""
        start_time = time.time()
        
        try:
            # Извлекаем текст из PDF
            extracted_text = await self._extract_text_from_pdf(pdf_bytes)
            
            # Структурируем данные резюме
            resume_data = await self._extract_resume_data(extracted_text)
            
            processing_time = time.time() - start_time
            print(f"✅ PDF обработан за {processing_time:.2f} секунд")
            
            return extracted_text, resume_data
            
        except Exception as e:
            print(f"❌ Ошибка обработки PDF: {e}")
            raise
    
    async def _extract_text_from_pdf(self, pdf_bytes: bytes) -> List[ExtractedText]:
        """Извлечение текста из PDF с помощью OCR"""
        extracted_text = []
        
        try:
            # Сначала пробуем извлечь текст напрямую из PDF
            pdf_text = await self._extract_pdf_text(pdf_bytes)
            
            if pdf_text and any(len(text.strip()) > 50 for text in pdf_text):
                # Если текст извлечен успешно, используем его
                for i, text in enumerate(pdf_text):
                    if text.strip():
                        extracted_text.append(ExtractedText(
                            page_number=i + 1,
                            text=text.strip(),
                            confidence=1.0,  # PDF текст имеет 100% уверенность
                            bounding_boxes=None
                        ))
                print(f"📄 Извлечен текст из {len(extracted_text)} страниц PDF")
                return extracted_text
            
            # Если PDF текст не извлечен, используем OCR
            print("🔍 Используем OCR для извлечения текста...")
            extracted_text = await self._ocr_extraction(pdf_bytes)
            
        except Exception as e:
            print(f"❌ Ошибка извлечения текста: {e}")
            raise
        
        return extracted_text
    
    async def _extract_pdf_text(self, pdf_bytes: bytes) -> List[str]:
        """Извлечение текста напрямую из PDF"""
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            texts = []
            for page in pdf_reader.pages:
                text = page.extract_text()
                texts.append(text)
            
            return texts
            
        except Exception as e:
            print(f"⚠️ Не удалось извлечь текст из PDF: {e}")
            return []
    
    async def _ocr_extraction(self, pdf_bytes: bytes) -> List[ExtractedText]:
        """OCR извлечение текста из PDF"""
        extracted_text = []
        
        try:
            # Конвертируем PDF в изображения
            images = convert_from_bytes(pdf_bytes, dpi=300)
            print(f"🖼️ PDF конвертирован в {len(images)} изображений")
            
            for i, image in enumerate(images):
                print(f"🔍 Обрабатываю страницу {i + 1}/{len(images)}...")
                
                # Предобработка изображения
                processed_image = await self._preprocess_image(image)
                
                # OCR извлечение
                text, confidence, boxes = await self._extract_text_from_image(processed_image)
                
                extracted_text.append(ExtractedText(
                    page_number=i + 1,
                    text=text,
                    confidence=confidence,
                    bounding_boxes=boxes
                ))
                
                print(f"   Страница {i + 1}: {len(text)} символов, уверенность: {confidence:.2f}")
            
        except Exception as e:
            print(f"❌ Ошибка OCR извлечения: {e}")
            raise
        
        return extracted_text
    
    async def _preprocess_image(self, image: Image.Image) -> np.ndarray:
        """Предобработка изображения для улучшения OCR"""
        try:
            # Конвертируем в numpy array
            img_array = np.array(image)
            
            # Конвертируем в grayscale если нужно
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # Увеличиваем контраст
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            
            # Убираем шум
            denoised = cv2.fastNlMeansDenoising(enhanced)
            
            # Бинаризация
            _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            return binary
            
        except Exception as e:
            print(f"⚠️ Ошибка предобработки изображения: {e}")
            return np.array(image)
    
    async def _extract_text_from_image(self, image: np.ndarray) -> Tuple[str, float, List[Dict[str, Any]]]:
        """Извлечение текста из изображения с помощью Tesseract"""
        try:
            # OCR извлечение
            ocr_data = pytesseract.image_to_data(
                image, 
                config=self.tesseract_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Собираем текст и координаты
            text_parts = []
            bounding_boxes = []
            
            for i in range(len(ocr_data['text'])):
                if int(ocr_data['conf'][i]) > 30:  # Фильтруем по уверенности
                    text = ocr_data['text'][i].strip()
                    if text:
                        text_parts.append(text)
                        
                        # Координаты блока
                        box = {
                            'x': ocr_data['left'][i],
                            'y': ocr_data['top'][i],
                            'width': ocr_data['width'][i],
                            'height': ocr_data['height'][i],
                            'confidence': int(ocr_data['conf'][i]) / 100.0
                        }
                        bounding_boxes.append(box)
            
            full_text = ' '.join(text_parts)
            
            # Вычисляем среднюю уверенность
            avg_confidence = np.mean([box['confidence'] for box in bounding_boxes]) if bounding_boxes else 0.0
            
            return full_text, avg_confidence, bounding_boxes
            
        except Exception as e:
            print(f"⚠️ Ошибка OCR извлечения: {e}")
            return "", 0.0, []
    
    async def _extract_resume_data(self, extracted_text: List[ExtractedText]) -> ResumeData:
        """Извлечение структурированных данных из текста резюме"""
        try:
            # Объединяем весь текст
            full_text = '\n'.join([et.text for et in extracted_text])
            
            # Извлекаем данные по паттернам
            extracted_data = {}
            
            for field, patterns in self.patterns.items():
                for pattern in patterns:
                    match = re.search(pattern, full_text, re.IGNORECASE | re.MULTILINE)
                    if match:
                        if field == 'name':
                            extracted_data[field] = match.group(1).strip()
                        elif field == 'email':
                            extracted_data[field] = match.group(0).strip()
                        elif field == 'phone':
                            extracted_data[field] = match.group(0).strip()
                        else:
                            extracted_data[field] = match.group(1).strip() if match.groups() else match.group(0).strip()
                        break
            
            # Дополнительная обработка навыков
            skills = self._extract_skills_from_text(full_text)
            if skills:
                extracted_data['skills'] = skills
            
            # Дополнительная обработка языков
            languages = self._extract_languages_from_text(full_text)
            if languages:
                extracted_data['languages'] = languages
            
            # Создаем объект ResumeData
            resume_data = ResumeData(
                name=extracted_data.get('name'),
                email=extracted_data.get('email'),
                phone=extracted_data.get('phone'),
                experience=extracted_data.get('experience'),
                education=extracted_data.get('education'),
                skills=extracted_data.get('skills', []),
                languages=extracted_data.get('languages', []),
                summary=self._extract_summary(full_text),
                raw_text=full_text
            )
            
            print(f"📋 Извлечены данные: {', '.join([k for k, v in extracted_data.items() if v])}")
            
            return resume_data
            
        except Exception as e:
            print(f"❌ Ошибка извлечения данных резюме: {e}")
            # Возвращаем базовый объект с сырым текстом
            full_text = '\n'.join([et.text for et in extracted_text])
            return ResumeData(raw_text=full_text)
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Извлечение навыков из текста"""
        skills = []
        
        # Паттерны для навыков
        skill_patterns = [
            r'Python', r'Java', r'JavaScript', r'React', r'Angular', r'Vue',
            r'Node\.js', r'Django', r'Flask', r'FastAPI', r'PostgreSQL', r'MySQL',
            r'MongoDB', r'Redis', r'Docker', r'Kubernetes', r'Git', r'Linux',
            r'SQL', r'HTML', r'CSS', r'TypeScript', r'C\+\+', r'C#', r'Go',
            r'Rust', r'PHP', r'Ruby', r'Swift', r'Kotlin', r'Scala'
        ]
        
        for pattern in skill_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                skills.append(pattern)
        
        return list(set(skills))  # Убираем дубликаты
    
    def _extract_languages_from_text(self, text: str) -> List[str]:
        """Извлечение языков из текста"""
        languages = []
        
        # Паттерны для языков
        language_patterns = [
            r'Английский[:\s]+([A-Za-z]+)', r'English[:\s]+([A-Za-z]+)',
            r'Немецкий[:\s]+([A-Za-z]+)', r'German[:\s]+([A-Za-z]+)',
            r'Французский[:\s]+([A-Za-z]+)', r'French[:\s]+([A-Za-z]+)',
            r'Испанский[:\s]+([A-Za-z]+)', r'Spanish[:\s]+([A-Za-z]+)',
            r'Китайский[:\s]+([A-Za-z]+)', r'Chinese[:\s]+([A-Za-z]+)',
        ]
        
        for pattern in language_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                languages.append(match.group(1))
        
        return list(set(languages))
    
    def _extract_summary(self, text: str) -> Optional[str]:
        """Извлечение краткого описания"""
        # Ищем первые 2-3 предложения
        sentences = re.split(r'[.!?]+', text)
        summary_sentences = [s.strip() for s in sentences[:3] if len(s.strip()) > 20]
        
        if summary_sentences:
            return '. '.join(summary_sentences) + '.'
        return None
