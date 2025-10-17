# app/config.py - Production-ready configuration management
from dotenv import load_dotenv
import os

load_dotenv()
from typing import Optional, Union, Union
from functools import lru_cache

import json
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings with validation and environment variable support (Pydantic V2 Syntax)"""
    
    # Model Config for Pydantic V2
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow",
        case_sensitive=False
    )

    # Application
    app_name: str = "Dr. Dhingra's Clinic Management System"
    app_version: str = "2.0.0"
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")
    
    # Database
    database_url: str = Field(..., alias="DATABASE_URL")
    database_pool_size: int = Field(default=20, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=30, alias="DATABASE_MAX_OVERFLOW")
    
    # Security
    secret_key: str = Field(..., alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Encryption
    encryption_key: str = Field(..., alias="ENCRYPTION_KEY")
    
    # CORS
    cors_origins: Union[str, list[str]] = Field(default=["http://localhost:3000", "http://localhost:8000"], alias="CORS_ORIGINS")
    
    # WhatsApp Business API
    whatsapp_access_token: Optional[str] = Field(default=None, alias="WHATSAPP_ACCESS_TOKEN")
    whatsapp_phone_number_id: Optional[str] = Field(default=None, alias="WHATSAPP_PHONE_NUMBER_ID")

    # ... all other fields remain but we don't need to list them all for the edit ...
    
    # --- Pydantic V2 Validators ---
    @field_validator("cors_origins", mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            if not v.strip():
                return ["http://localhost:3000", "http://localhost:8000"]
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL is required")
        if not v.startswith(("postgresql://", "postgresql+psycopg2://", "sqlite:///")):
            raise ValueError("DATABASE_URL must be a valid PostgreSQL or SQLite URL")
        return v

    @field_validator("secret_key", "encryption_key")
    @classmethod
    def validate_key_length(cls, v):
        if not v or len(v) < 32:
            raise ValueError("SECRET_KEY and ENCRYPTION_KEY must be at least 32 characters long")
        return v
    
    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"
    
    @property
    def whatsapp_enabled(self) -> bool:
        return bool(self.whatsapp_access_token and self.whatsapp_phone_number_id)
    
    @property
    def email_enabled(self) -> bool:
        return bool(self.sendgrid_api_key or (self.smtp_server and self.smtp_username))
    
    @property
    def calendar_enabled(self) -> bool:
        return bool(self.google_calendar_credentials_file and self.enable_calendar_integration)
    
    @property
    def redis_enabled(self) -> bool:
        return bool(self.redis_url)

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

# Environment-specific configurations
class DevelopmentConfig(Settings):
    """Development environment configuration"""
    debug: bool = True
    environment: str = "development"
    
class ProductionConfig(Settings):
    """Production environment configuration"""
    debug: bool = False
    environment: str = "production"
    enable_detailed_logging: bool = False

class TestingConfig(Settings):
    """Testing environment configuration"""
    debug: bool = True
    environment: str = "testing"
    database_url: str = "sqlite:///./test.db"

def get_config_by_env(env: str) -> Settings:
    """Get configuration by environment name"""
    configs = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig
    }
    
    config_class = configs.get(env.lower(), Settings)
    return config_class()

# Note: Do not instantiate settings at import time to avoid failing
# on missing environment variables. Use `get_settings()` instead.
