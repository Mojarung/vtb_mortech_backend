#!/usr/bin/env python3
"""
СКРИПТ ДЛЯ СОЗДАНИЯ ВСЕХ ТАБЛИЦ В БАЗЕ ДАННЫХ
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Данные подключения
DATABASE_URL = "postgres://u8pabi5s6v7nnp:p799258912088002fb9684b5afe72def72326c7b545aab369b533159a18f1487c@c18qegamsgjut6.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/dfsb5dl3s8q27s"

def create_tables():
    """Создает все таблицы в базе данных"""
    
    print("🚀 СОЗДАНИЕ ВСЕХ ТАБЛИЦ")
    print("=" * 40)
    
    try:
        # Подключаемся
        print("🔌 Подключение...")
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("✅ Подключен!")
        
        # Создаем enum типы
        print("📝 Создание enum типов...")
        
        cursor.execute("""
            CREATE TYPE userrole AS ENUM ('hr', 'user');
        """)
        print("✅ userrole")
        
        cursor.execute("""
            CREATE TYPE employmenttype AS ENUM ('full_time', 'part_time', 'contract', 'freelance', 'internship');
        """)
        print("✅ employmenttype")
        
        cursor.execute("""
            CREATE TYPE vacancystatus AS ENUM ('open', 'closed');
        """)
        print("✅ vacancystatus")
        
        cursor.execute("""
            CREATE TYPE interviewstatus AS ENUM ('not_started', 'in_progress', 'completed');
        """)
        print("✅ interviewstatus")
        
        cursor.execute("""
            CREATE TYPE applicationstatus AS ENUM ('pending', 'interview_scheduled', 'interview_completed', 'accepted', 'rejected');
        """)
        print("✅ applicationstatus")
        
        cursor.execute("""
            CREATE TYPE processingstatus AS ENUM ('pending', 'processing', 'completed', 'failed');
        """)
        print("✅ processingstatus")
        
        # Создаем таблицу users
        print("\n📝 Создание таблицы users...")
        cursor.execute("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                username VARCHAR UNIQUE NOT NULL,
                email VARCHAR UNIQUE NOT NULL,
                hashed_password VARCHAR NOT NULL,
                role userrole NOT NULL DEFAULT 'user',
                full_name VARCHAR,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                first_name VARCHAR,
                last_name VARCHAR,
                phone VARCHAR,
                birth_date DATE,
                location VARCHAR,
                about TEXT,
                desired_salary INTEGER,
                ready_to_relocate BOOLEAN DEFAULT FALSE,
                employment_type employmenttype,
                education JSON,
                skills JSON,
                work_experience JSON
            );
        """)
        print("✅ users")
        
        # Создаем таблицу vacancies
        print("📝 Создание таблицы vacancies...")
        cursor.execute("""
            CREATE TABLE vacancies (
                id SERIAL PRIMARY KEY,
                title VARCHAR NOT NULL,
                description TEXT NOT NULL,
                requirements TEXT,
                salary_from INTEGER,
                salary_to INTEGER,
                location VARCHAR,
                employment_type VARCHAR,
                experience_level VARCHAR,
                benefits TEXT,
                company VARCHAR(255),
                status vacancystatus DEFAULT 'open',
                original_url VARCHAR,
                creator_id INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                auto_interview_enabled BOOLEAN DEFAULT FALSE,
                auto_interview_threshold INTEGER DEFAULT 70
            );
        """)
        print("✅ vacancies")
        
        # Создаем таблицу resumes
        print("📝 Создание таблицы resumes...")
        cursor.execute("""
            CREATE TABLE resumes (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                vacancy_id INTEGER REFERENCES vacancies(id),
                file_path VARCHAR NOT NULL,
                original_filename VARCHAR NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT FALSE,
                uploaded_by_hr BOOLEAN DEFAULT FALSE,
                status applicationstatus DEFAULT 'pending',
                processing_status processingstatus DEFAULT 'pending',
                notes TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                hidden_for_hr BOOLEAN DEFAULT FALSE
            );
        """)
        print("✅ resumes")
        
        # Создаем таблицу resume_analyses
        print("📝 Создание таблицы resume_analyses...")
        cursor.execute("""
            CREATE TABLE resume_analyses (
                id SERIAL PRIMARY KEY,
                resume_id INTEGER UNIQUE REFERENCES resumes(id),
                name VARCHAR,
                position VARCHAR,
                experience VARCHAR,
                education VARCHAR,
                upload_date VARCHAR,
                match_score VARCHAR,
                key_skills JSON,
                recommendation VARCHAR,
                projects JSON,
                work_experience JSON,
                technologies JSON,
                achievements JSON,
                strengths JSON,
                weaknesses JSON,
                missing_skills JSON,
                brief_reason TEXT,
                structured BOOLEAN,
                effort_level VARCHAR,
                suspicious_phrases_found BOOLEAN,
                suspicious_examples JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("✅ resume_analyses")
        
        # Создаем таблицу interviews
        print("📝 Создание таблицы interviews...")
        cursor.execute("""
            CREATE TABLE interviews (
                id SERIAL PRIMARY KEY,
                vacancy_id INTEGER REFERENCES vacancies(id),
                resume_id INTEGER REFERENCES resumes(id),
                status interviewstatus DEFAULT 'not_started',
                scheduled_date TIMESTAMP,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                duration_minutes INTEGER,
                dialogue JSON,
                summary TEXT,
                pass_percentage FLOAT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("✅ interviews")
        
        # Создаем индексы
        print("\n📝 Создание индексов...")
        cursor.execute("CREATE INDEX ix_users_id ON users (id);")
        cursor.execute("CREATE INDEX ix_users_username ON users (username);")
        cursor.execute("CREATE INDEX ix_users_email ON users (email);")
        cursor.execute("CREATE INDEX ix_vacancies_id ON vacancies (id);")
        cursor.execute("CREATE INDEX ix_resumes_id ON resumes (id);")
        cursor.execute("CREATE INDEX ix_resume_analyses_id ON resume_analyses (id);")
        cursor.execute("CREATE INDEX ix_interviews_id ON interviews (id);")
        print("✅ Индексы созданы")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 40)
        print("🎉 ВСЕ ТАБЛИЦЫ СОЗДАНЫ!")
        print("📊 Создано:")
        print("   - 6 enum типов")
        print("   - 5 таблиц")
        print("   - 7 индексов")
        print("✅ База данных готова к работе!")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    try:
        success = create_tables()
        if success:
            print("\n🚀 ГОТОВО!")
        else:
            print("\n❌ ОШИБКА!")
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
