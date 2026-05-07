from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    PROJECT_NAME: str = "Symphony Lite"
    VERSION: str = "0.1.0"
    
    DATABASE_URL: str = "postgresql+psycopg2://symphony:symphony@localhost:5432/symphony"
    
    SECRET_KEY: str = "change-me-in-production-symphony-lite-secret-key-2025"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7일
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
