#!/usr/bin/env python3
"""
Скрипт для миграции базы данных - добавление AI полей в таблицу vacancy_applications
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.db.session import engine

async def migrate_ai_fields():
    """Добавляет AI поля в таблицу vacancy_applications"""
    try:
        async with engine.begin() as conn:
            print("🚀 Начинаем миграцию базы данных для AI полей...")
            
            # Проверяем существование таблицы
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'vacancy_applications'
                );
            """))
            
            table_exists = result.scalar()
            if not table_exists:
                print("❌ Таблица vacancy_applications не существует!")
                return
            
            # Добавляем AI поля
            migration_sql = """
            ALTER TABLE vacancy_applications 
            ADD COLUMN IF NOT EXISTS resume_file_path VARCHAR(500),
            ADD COLUMN IF NOT EXISTS resume_file_name VARCHAR(255),
            ADD COLUMN IF NOT EXISTS resume_file_size INTEGER,
            ADD COLUMN IF NOT EXISTS cover_letter TEXT,
            ADD COLUMN IF NOT EXISTS notes TEXT,
            ADD COLUMN IF NOT EXISTS ai_recommendation TEXT,
            ADD COLUMN IF NOT EXISTS ai_match_percentage INTEGER,
            ADD COLUMN IF NOT EXISTS ai_analysis_date TIMESTAMP,
            ADD COLUMN IF NOT EXISTS interview_date TIMESTAMP,
            ADD COLUMN IF NOT EXISTS interview_link VARCHAR(500),
            ADD COLUMN IF NOT EXISTS interview_notes TEXT,
            ADD COLUMN IF NOT EXISTS status_updated_at TIMESTAMP;
            """
            
            await conn.execute(text(migration_sql))
            
            print("✅ Миграция выполнена успешно!")
            print("\n📋 Добавлены следующие поля:")
            print("   📄 resume_file_path (VARCHAR(500)) - Путь к PDF файлу резюме")
            print("   📄 resume_file_name (VARCHAR(255)) - Имя файла резюме")
            print("   📄 resume_file_size (INTEGER) - Размер файла в байтах")
            print("   💬 cover_letter (TEXT) - Сопроводительное письмо")
            print("   📝 notes (TEXT) - Заметки HR и AI анализ")
            print("   🤖 ai_recommendation (TEXT) - Рекомендация от ИИ")
            print("   📊 ai_match_percentage (INTEGER) - Процент соответствия (0-100)")
            print("   🕒 ai_analysis_date (TIMESTAMP) - Дата анализа ИИ")
            print("   📅 interview_date (TIMESTAMP) - Дата интервью")
            print("   🔗 interview_link (VARCHAR(500)) - Ссылка на интервью")
            print("   📝 interview_notes (TEXT) - Заметки по интервью")
            print("   🕒 status_updated_at (TIMESTAMP) - Дата изменения статуса")
            
            print("\n🎉 Система готова для работы с AI анализом резюме!")
            
    except Exception as e:
        print(f"❌ Ошибка при выполнении миграции: {e}")
        raise

if __name__ == "__main__":
    print("🔧 Миграция базы данных для AI интеграции")
    print("=" * 50)
    asyncio.run(migrate_ai_fields())
