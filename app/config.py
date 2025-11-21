from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///:memory:"
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET: str = "test-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    HOLD_TTL_SECONDS: int = 600
    CANCELLATION_WINDOW_MINUTES: int = 60

    model_config = ConfigDict(env_file='.env')


settings = Settings()
