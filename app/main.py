from __future__ import annotations

import asyncio

from fastapi import FastAPI

from app.api import auth as auth_router
from app.api import users as users_router
from app.api import ocr as ocr_router
from app.api import vacancies as vacancies_router
from app.api import interviews as interviews_router
from app.db.session import Base, engine

app = FastAPI(title="VTB Mortech Backend")


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(ocr_router.router)
app.include_router(vacancies_router.router)
app.include_router(interviews_router.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}