from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://booking:booking@localhost:5432/booking"
    test_database_url: str = "postgresql+asyncpg://booking:booking@localhost:5432/booking_test"
    redis_url: str = "redis://localhost:6379/0"


settings = Settings()
