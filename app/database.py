from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
from app.config import settings

# Кодируем пароль для URL
encoded_password = quote_plus(settings.database_password)

DATABASE_URL = (
    f"postgresql://{settings.database_user}:{encoded_password}"
    f"@{settings.database_host}/{settings.database_name}"
)

print(f"Подключение к базе: postgresql://{settings.database_user}:***@{settings.database_host}/{settings.database_name}")

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