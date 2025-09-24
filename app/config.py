from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from functools import lru_cache
import secrets

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")
    
    # Database
    database_url: str = Field(..., description="Database connection URL")
    
    # Security
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    access_token_expire_minutes: int = Field(default=30, ge=1, le=10080)
    
    # Email
    sendgrid_api_key: str = "dummy"
    sender_email: str = "dummy@thecodingskool.com"
    sender_password: str = ""
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    
    # WhatsApp
    whatsapp_phone_id: str = ""
    whatsapp_access_token: str = ""
    
    # CORS
    allowed_origins: List[str] = Field(default=["http://localhost:8000", "http://localhost:3000"])
    
    # Monitoring
    enable_metrics: bool = Field(default=True)
    log_level: str = Field(default="INFO")
    
    # Performance
    db_pool_size: int = Field(default=20, ge=5, le=100)
    db_max_overflow: int = Field(default=30, ge=5, le=100)
    
    # Extra app settings
    app_name: str = Field(default="MyApp")
    debug: bool = Field(default=False)

    @field_validator("database_url")
    def validate_database_url(cls, v):
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("Database URL must be PostgreSQL")
        return v


@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
