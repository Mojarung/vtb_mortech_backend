from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "VTB Mortech Backend"
    debug: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///./app.db"

    # Security
    secret_key: str = "Скока скока скока 🤔🤔🤔дряни лежит🤮🤮🤮В твоей новой сумке от дизель ⛽️Так сильна 💪👍  меня любишь 💋💋Так начинаний ненавидеть 👎👎👎👎"
    access_token_expire_minutes: int = 60 * 24
    algorithm: str = "HS256"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", case_sensitive=False)


settings = Settings()
