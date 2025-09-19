-- Удаление всех таблиц (если есть)
DROP TABLE IF EXISTS interviews CASCADE;
DROP TABLE IF EXISTS resume_analyses CASCADE;
DROP TABLE IF EXISTS resumes CASCADE;
DROP TABLE IF EXISTS vacancies CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS alembic_version CASCADE;

-- Удаление всех типов данных
DROP TYPE IF EXISTS processingstatus CASCADE;
DROP TYPE IF EXISTS applicationstatus CASCADE;
DROP TYPE IF EXISTS interviewstatus CASCADE;
DROP TYPE IF EXISTS vacancystatus CASCADE;
DROP TYPE IF EXISTS employmenttype CASCADE;
DROP TYPE IF EXISTS userrole CASCADE;

-- Создание типов данных заново
CREATE TYPE userrole AS ENUM ('HR', 'USER');
CREATE TYPE employmenttype AS ENUM ('FULL_TIME', 'PART_TIME', 'CONTRACT', 'FREELANCE', 'INTERNSHIP');
CREATE TYPE vacancystatus AS ENUM ('OPEN', 'CLOSED');
CREATE TYPE interviewstatus AS ENUM ('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED');
CREATE TYPE applicationstatus AS ENUM ('PENDING', 'INTERVIEW_SCHEDULED', 'INTERVIEW_COMPLETED', 'ACCEPTED', 'REJECTED');
CREATE TYPE processingstatus AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED');

-- Создание таблицы users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    role userrole NOT NULL DEFAULT 'USER',
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

-- Создание индексов для users
CREATE INDEX ix_users_id ON users (id);
CREATE INDEX ix_users_username ON users (username);
CREATE INDEX ix_users_email ON users (email);

-- Создание таблицы vacancies
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
    status vacancystatus DEFAULT 'OPEN',
    original_url VARCHAR,
    creator_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    auto_interview_enabled BOOLEAN DEFAULT FALSE
);

-- Создание индексов для vacancies
CREATE INDEX ix_vacancies_id ON vacancies (id);

-- Создание таблицы resumes
CREATE TABLE resumes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    vacancy_id INTEGER REFERENCES vacancies(id),
    file_path VARCHAR NOT NULL,
    original_filename VARCHAR NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE,
    uploaded_by_hr BOOLEAN DEFAULT FALSE,
    status applicationstatus DEFAULT 'PENDING',
    processing_status processingstatus DEFAULT 'PENDING',
    notes TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hidden_for_hr BOOLEAN DEFAULT FALSE
);

-- Создание индексов для resumes
CREATE INDEX ix_resumes_id ON resumes (id);

-- Создание таблицы resume_analyses
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

-- Создание индексов для resume_analyses
CREATE INDEX ix_resume_analyses_id ON resume_analyses (id);

-- Создание таблицы interviews
CREATE TABLE interviews (
    id SERIAL PRIMARY KEY,
    vacancy_id INTEGER REFERENCES vacancies(id),
    resume_id INTEGER REFERENCES resumes(id),
    status interviewstatus DEFAULT 'NOT_STARTED',
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

-- Создание индексов для interviews
CREATE INDEX ix_interviews_id ON interviews (id);

-- Создание таблицы alembic_version для отслеживания миграций
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Вставка текущей версии миграции
INSERT INTO alembic_version (version_num) VALUES ('372e22afa8cc');
