from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Add these two lines
    DATABASE_URL: str
    SENDGRID_API_KEY: str = "YOUR_KEY_FOR_DEVELOPMENT"


    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    """
    This function creates and caches the settings instance.
    Using lru_cache ensures this is only run once.
    """
    return Settings()
