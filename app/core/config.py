from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "VTB Mortech Backend"
    debug: bool = False
    
    # PostgreSQL (облако)
    postgres_host: str = "94.228.113.42"
    postgres_database: str = "default_db"
    postgres_user: str = "admin_1"
    postgres_password: str = "hppKD~s@S75;e="

    # Security
    secret_key: str = "Скока скока скока 🤔🤔🤔дряни лежит🤮🤮🤮В твоей новой сумке от дизель ⛽️Так сильна 💪👍  меня любишь 💋💋Так начинаний ненавидеть 👎👎👎👎"
    access_token_expire_minutes: int = 60 * 24
    algorithm: str = "HS256"
    
    # AI Service (OpenRouter)
    openrouter_api_key: str = "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"
    openrouter_model: str = "anthropic/claude-3.5-sonnet"  # Модель по умолчанию
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_",
        case_sensitive=False
    )


settings = Settings()