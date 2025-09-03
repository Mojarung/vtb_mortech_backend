from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


class Base(DeclarativeBase):
    pass


# Создаем async engine для PostgreSQL
engine = create_async_engine(
    "postgresql+asyncpg://",  # Пустой URL
    echo=settings.debug,
    connect_args={
        "host": settings.postgres_host,
        "port": 5432,
        "database": settings.postgres_database,
        "user": settings.postgres_user,
        "password": settings.postgres_password,
        "ssl": False  # отключаем SSL как в тесте
    }
)

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Получение сессии БД"""
    async with AsyncSessionLocal() as session:
        yield session


async def create_tables():
    """Создание таблиц в БД"""
    if engine is None:
        init_db()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Закрытие подключения к БД"""
    global engine
    if engine:
        await engine.dispose()
        engine = None