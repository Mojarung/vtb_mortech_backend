from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, vacancies, resumes, interviews

app = FastAPI(title="VTB HR Backend", version="1.0.0")

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

@app.get("/")
async def root():
    return {"message": "VTB HR Backend API"}