"""
Сервис для парсинга PDF резюме
"""

import PyPDF2
import pdfplumber
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class PDFService:
    """Сервис для извлечения текста из PDF файлов"""
    
    @staticmethod
    def extract_text_from_pdf(pdf_path: str) -> str:
        """
        Извлекает текст из PDF файла
        """
        try:
            # Пробуем сначала pdfplumber (лучше для таблиц и сложной верстки)
            text = PDFService._extract_with_pdfplumber(pdf_path)
            if text and len(text.strip()) > 50:  # Если получили достаточно текста
                return text
            
            # Если pdfplumber не сработал, пробуем PyPDF2
            text = PDFService._extract_with_pypdf2(pdf_path)
            if text and len(text.strip()) > 50:
                return text
            
            logger.warning(f"Could not extract meaningful text from PDF: {pdf_path}")
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
            return ""
    
    @staticmethod
    def _extract_with_pdfplumber(pdf_path: str) -> str:
        """Извлечение текста с помощью pdfplumber"""
        try:
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip()
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")
            return ""
    
    @staticmethod
    def _extract_with_pypdf2(pdf_path: str) -> str:
        """Извлечение текста с помощью PyPDF2"""
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip()
        except Exception as e:
            logger.warning(f"PyPDF2 extraction failed: {e}")
            return ""
    
    @staticmethod
    def get_pdf_info(pdf_path: str) -> Dict[str, Any]:
        """
        Получает информацию о PDF файле
        """
        try:
            info = {
                "file_size": 0,
                "page_count": 0,
                "has_text": False,
                "extraction_successful": False
            }
            
            # Размер файла
            file_path = Path(pdf_path)
            if file_path.exists():
                info["file_size"] = file_path.stat().st_size
            
            # Количество страниц и проверка текста
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    info["page_count"] = len(pdf.pages)
                    
                    # Проверяем первую страницу на наличие текста
                    if pdf.pages:
                        first_page_text = pdf.pages[0].extract_text()
                        info["has_text"] = bool(first_page_text and first_page_text.strip())
                        
            except Exception as e:
                logger.warning(f"Could not get PDF info: {e}")
            
            # Проверяем успешность извлечения
            extracted_text = PDFService.extract_text_from_pdf(pdf_path)
            info["extraction_successful"] = len(extracted_text.strip()) > 50
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting PDF info: {e}")
            return {
                "file_size": 0,
                "page_count": 0,
                "has_text": False,
                "extraction_successful": False
            }
