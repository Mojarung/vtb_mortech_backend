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
    api_key: str = "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCIsImtpZCI6IjFrYnhacFJNQGJSI0tSbE1xS1lqIn0.eyJ1c2VyIjoiaHg4NTczOCIsInR5cGUiOiJhcGlfa2V5IiwiYXBpX2tleV9pZCI6ImNiYWIxZDcxLWJiYzctNGYxNS1iMzYyLTM3ZTUxOGFhNDlkZCIsImlhdCI6MTc1NzIzNTUyN30.vMILt4d_q4Vx3IHIhSrQ9tmY1L5bVWdDEhxCfyeTh-KdepsYh6viFkUg9BxBiD8jzpNppIIIxsaSYz-9CfsqOR7fesVbSdxEzcGfrUTaepgzceNSeJMLR-n-WOBzlNm6tBHuy8aUzvuVx2paGmM1fbFm4p5kPiOE1MuIajuKJUmcVAjv8nLR-cAQM-5PfKiRfivUVLe4RmwOmtXQWdTttEQJq3MZnWSISmzpogsDtXNkiSPJTxttP8BR3vIbRVUf6ss_YcNBdTMBSLO6DV6sum3EaWZadvZROc0eMD4cldtWfvN1Vh_5EDcWSVwxesFDni3J-Nk82rwlgJpUhY8NYv-cIGjrtwjbq2nEhy-hhb0hwaO4G9Xdqqrh2xg416BVkz8an4yxN-bLTjY_r-z1acoaAS-UAnCr9GtjYRc6LUMOWG0jNM2d5b_9iyE303QlEQfBHsBOONSCKOI1S3wSnwzrA6xfmlDClZiZp7Qi44mLx-iMXARttwn2Dr4gbs3R"
    base_url: str = "https://agent.timeweb.cloud"
    
    class Config:
        # Убираем зависимость от .env файла - используем только переменные окружения
        case_sensitive = False

settings = Settings()
