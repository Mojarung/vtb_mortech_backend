from __future__ import annotations

from fastapi import FastAPI

from app.api import auth as auth_router
from app.api import users as users_router
from app.api import ocr as ocr_router
from app.api import vacancies as vacancies_router
from app.api import interviews as interviews_router


def create_app() -> FastAPI:
    app = FastAPI(title="VTB Mortech Backend")
    app.include_router(auth_router.router)
    app.include_router(users_router.router)
    app.include_router(ocr_router.router)
    app.include_router(vacancies_router.router)
    app.include_router(interviews_router.router)
    return app


