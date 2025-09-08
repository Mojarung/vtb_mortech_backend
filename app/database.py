from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
from app.config import settings

# Прямое подключение к базе данных (приоритет над настройками)
DIRECT_DATABASE_URL = "postgresql://admin_1:jopabobra@94.228.113.42/mortech"

# Кодируем пароль для URL (резервный вариант)
encoded_password = quote_plus(settings.database_password)

DATABASE_URL = DIRECT_DATABASE_URL or (
    f"postgresql://{settings.database_user}:{encoded_password}"
    f"@{settings.database_host}/{settings.database_name}"
)

print(f"Используется прямое подключение: postgresql://admin_1:jopabobra@94.228.113.42/mortech")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Создание всех таблиц при запуске
def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()