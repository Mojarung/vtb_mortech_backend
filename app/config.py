from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Не используем .env по умолчанию на проде (Heroku), читаем только окружение
    model_config = SettingsConfigDict(env_file=None, case_sensitive=False)

    # Безопасные значения по умолчанию оставлены, секреты и внешние адреса — только из окружения
    secret_key: str = Field(..., validation_alias="SECRET_KEY", description="JWT secret key")
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


settings = Settings()
