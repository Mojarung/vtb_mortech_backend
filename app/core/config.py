from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "VTB Mortech Backend"
    debug: bool = False
    
    # PostgreSQL (облако)
    postgres_host: str = ""
    postgres_database: str = ""
    postgres_user: str = ""
    postgres_password: str = ""

    # Security
    secret_key: str = ""
    access_token_expire_minutes: int = 60 * 24
    algorithm: str = "HS256"
    
    # AI Service (OpenRouter)
    openrouter_api_key: str = ""
    openrouter_model: str = "anthropic/claude-3.5-sonnet"  # Модель по умолчанию

    # External services
    ocr_service_url: str = "http://localhost:8001"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_",
        case_sensitive=False
    )


settings = Settings()