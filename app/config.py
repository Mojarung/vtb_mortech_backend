import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    database_host: str = "94.228.113.42"
    database_name: str = "mortech"
    database_user: str = "admin_1"
    database_password: str = r"hppKD~s@S75;e="
    
    upload_dir: str = "uploads"
    
    class Config:
        env_file = ".env"

settings = Settings()
