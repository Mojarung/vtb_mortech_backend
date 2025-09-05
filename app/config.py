import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Настройки базы данных (могут переопределяться переменными окружения)
    database_host: str = "94.228.113.42"
    database_name: str = "mortech"
    database_user: str = "admin_1"
    database_password: str = "jopabobra"
    
    upload_dir: str = "uploads"
    
    # Resume Analysis Service Configuration
    agent_id: str = ""
    api_key: str = ""
    base_url: str = "https://agent.timeweb.cloud"
    
    class Config:
        env_file = ".env"
        # Разрешаем переопределение переменными окружения
        case_sensitive = False

settings = Settings()
