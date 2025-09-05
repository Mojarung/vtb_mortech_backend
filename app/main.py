from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, vacancies, resumes, interviews
from app.database import create_tables
from app.logging_config import logger, log_startup, log_request
import time

app = FastAPI(title="VTB HR Backend", version="1.0.0")

# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Логируем входящий запрос
    log_request(f"{request.method} {request.url.path} - Client: {request.client.host if request.client else 'unknown'}")
    
    response = await call_next(request)
    
    # Логируем время выполнения
    process_time = time.time() - start_time
    logger.info(f"RESPONSE: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.4f}s")
    
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(vacancies.router, prefix="/vacancies", tags=["vacancies"])
app.include_router(resumes.router, prefix="/resumes", tags=["resumes"])
app.include_router(interviews.router, prefix="/interviews", tags=["interviews"])

@app.on_event("startup")
async def startup_event():
    log_startup("Приложение запускается...")
    create_tables()
    log_startup("Таблицы созданы успешно!")
    log_startup("VTB HR Backend готов к работе!")

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "VTB HR Backend API"}