import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60  # Увеличиваем время жизни токена для production
    
    # Настройки базы данных (могут переопределяться переменными окружения)
    database_host: str = "94.228.113.42"
    database_name: str = "mortech"
    database_user: str = "admin_1"
    database_password: str = "jopabobra"
    
    upload_dir: str = "uploads"
    
    # Resume Analysis Service Configuration
    agent_id: str = "7e7605da-7f02-4c74-8fa1-31c95dcbbab2"
    api_key: str = ""
    base_url: str = "https://agent.timeweb.cloud"
    
    class Config:
        # Убираем зависимость от .env файла - используем только переменные окружения
        case_sensitive = False

settings = Settings()
