from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Не используем .env по умолчанию на проде (Heroku), читаем только окружение
    model_config = SettingsConfigDict(env_file=None, case_sensitive=False)

    # Безопасные значения по умолчанию оставлены, секреты и внешние адреса — только из окружения
    secret_key: str = Field("your-secret-key-here-change-in-production", validation_alias="SECRET_KEY", description="JWT secret key")
    algorithm: str = Field("HS256", validation_alias="ALGORITHM")
    access_token_expire_minutes: int = Field(60, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    # Локальные настройки БД (fallback, если нет DATABASE_URL)
    database_host: str | None = Field(None, validation_alias="DATABASE_HOST")
    database_name: str | None = Field(None, validation_alias="DATABASE_NAME")
    database_user: str | None = Field(None, validation_alias="DATABASE_USER")
    database_password: str | None = Field(None, validation_alias="DATABASE_PASSWORD")

    upload_dir: str = Field("uploads", validation_alias="UPLOAD_DIR")

    # Настройки сервиса анализа резюме
    agent_id: str | None = Field(None, validation_alias="AGENT_ID")
    api_key: str | None = Field(None, validation_alias="API_KEY")
    base_url: str | None = Field(None, validation_alias="BASE_URL")

    # Конфигурация AI-провайдера для анализа резюме
    # Доступные значения: "openrouter", "heroku" (через совместимый Chat Completions API)
    # ai_provider: str | None = Field(None, validation_alias="AI_PROVIDER")

    # OpenRouter
    # openrouter_api_key: str | None = Field(None, validation_alias="OPENROUTER_API_KEY")
    # openrouter_base_url: str | None = Field("https://openrouter.ai/api/v1/chat/completions", validation_alias="OPENROUTER_BASE_URL")
    # openrouter_model: str | None = Field("deepseek/deepseek-r1:free", validation_alias="OPENROUTER_MODEL")

    # Heroku AI Inference (OpenAI-совместимый Chat Completions)
    heroku_ai_api_key: str | None = Field(None, validation_alias="INFERENCE_KEY")
    heroku_ai_base_url: str | None = Field(None, validation_alias="INFERENCE_URL")
    heroku_ai_model: str | None = Field(None, validation_alias="INFERENCE_MODEL_ID")


settings = Settings()
