import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Resume, ResumeAnalysis

async def process_resume(resume_id: int, db: Session):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        return
    
    mock_analysis_data = {
        "basic_info": {
            "name": "Иван Иванов",
            "position": "Frontend Developer",
            "experience": "3 года",
            "education": "МГУ, Прикладная математика",
            "upload_date": datetime.now().strftime("%Y-%m-%d"),
            "match_score": "92%",
            "key_skills": ["React", "TypeScript", "Next.js"],
            "recommendation": "Рекомендуется к интервью"
        },
        "extended_info": {
            "projects": ["Проект X (React + Node.js)", "Проект Y (ML pipeline)"],
            "work_experience": ["Frontend Dev в ABC (2 года)", "ML Intern в XYZ (1 год)"],
            "technologies": ["React", "Next.js", "TypeScript", "Python", "TensorFlow"],
            "achievements": ["Оптимизация фронтенда, ускорение загрузки на 30%", "Участие в хакатоне"]
        },
        "resume_quality": {
            "structured": True,
            "effort_level": "Высокий"
        },
        "anti_manipulation": {
            "suspicious_phrases_found": False,
            "examples": []
        }
    }
    
    analysis = ResumeAnalysis(
        resume_id=resume_id,
        name=mock_analysis_data["basic_info"]["name"],
        position=mock_analysis_data["basic_info"]["position"],
        experience=mock_analysis_data["basic_info"]["experience"],
        education=mock_analysis_data["basic_info"]["education"],
        upload_date=mock_analysis_data["basic_info"]["upload_date"],
        match_score=mock_analysis_data["basic_info"]["match_score"],
        key_skills=mock_analysis_data["basic_info"]["key_skills"],
        recommendation=mock_analysis_data["basic_info"]["recommendation"],
        projects=mock_analysis_data["extended_info"]["projects"],
        work_experience=mock_analysis_data["extended_info"]["work_experience"],
        technologies=mock_analysis_data["extended_info"]["technologies"],
        achievements=mock_analysis_data["extended_info"]["achievements"],
        structured=mock_analysis_data["resume_quality"]["structured"],
        effort_level=mock_analysis_data["resume_quality"]["effort_level"],
        suspicious_phrases_found=mock_analysis_data["anti_manipulation"]["suspicious_phrases_found"],
        suspicious_examples=mock_analysis_data["anti_manipulation"]["examples"]
    )
    
    db.add(analysis)
    resume.processed = True
    db.commit()
    db.refresh(analysis)
    return analysis
