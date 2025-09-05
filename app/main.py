from __future__ import annotations

import asyncio
import os
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth as auth_router
from app.api import users as users_router
from app.api import vacancies as vacancies_router
from app.api import applications as applications_router
from app.db.session import Base, engine
from app.services.ai_service import init_ai_service
from app.core.config import settings

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="VTB Mortech Backend")

# CORS for frontend on localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    # Создаем таблицы БД
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Инициализируем AI сервис (OpenRouter)
    try:
        init_ai_service(settings.openrouter_api_key, settings.openrouter_model)
        if settings.openrouter_api_key and settings.openrouter_api_key != "test":
            logger.info("OpenRouter AI service initialized successfully")
        else:
            logger.info("AI service initialized in test mode (no API key)")
    except Exception as e:
        logger.warning(f"Failed to initialize AI service: {e}")


app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(vacancies_router.router)
app.include_router(applications_router.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}