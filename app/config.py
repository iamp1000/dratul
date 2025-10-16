# app/config.py - Production-ready configuration management
import os
from typing import Optional
from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic import validator, Field, field_validator
from typing import Union


class Settings(BaseSettings):
    """Application settings with validation and environment variable support"""
    
    # Application
    app_name: str = "Dr. Dhingra's Clinic Management System"
    app_version: str = "2.0.0"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    database_pool_size: int = Field(default=20, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=30, env="DATABASE_MAX_OVERFLOW")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Encryption
    encryption_key: str = Field(..., env="ENCRYPTION_KEY")
    
    # CORS
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:8000", env="CORS_ORIGINS")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    # WhatsApp Business API
    whatsapp_access_token: Optional[str] = Field(default=None, env="WHATSAPP_ACCESS_TOKEN")
    whatsapp_phone_number_id: Optional[str] = Field(default=None, env="WHATSAPP_PHONE_NUMBER_ID")
    whatsapp_verify_token: str = Field(default="verify_token_123", env="WHATSAPP_VERIFY_TOKEN")
    whatsapp_webhook_url: Optional[str] = Field(default=None, env="WHATSAPP_WEBHOOK_URL")
    whatsapp_business_account_id: Optional[str] = Field(default=None, env="WHATSAPP_BUSINESS_ACCOUNT_ID")
    
    # Email Configuration (Multiple providers)
    # SendGrid
    sendgrid_api_key: Optional[str] = Field(default=None, env="SENDGRID_API_KEY")
    sendgrid_from_email: Optional[str] = Field(default=None, env="SENDGRID_FROM_EMAIL")
    
    # SMTP
    smtp_server: Optional[str] = Field(default=None, env="SMTP_SERVER")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, env="SMTP_USE_TLS")
    
    # Default email settings
    default_from_email: str = Field(default="noreply@clinic.com", env="DEFAULT_FROM_EMAIL")
    default_from_name: str = Field(default="Dr. Dhingra's Clinic", env="DEFAULT_FROM_NAME")
    
    # Google Calendar API
    google_calendar_credentials_file: Optional[str] = Field(default=None, env="GOOGLE_CALENDAR_CREDENTIALS_FILE")
    google_calendar_token_file: Optional[str] = Field(default="token.json", env="GOOGLE_CALENDAR_TOKEN_FILE")
    google_calendar_id: Optional[str] = Field(default="primary", env="GOOGLE_CALENDAR_ID")
    
    # Redis (for sessions and caching)
    redis_url: Optional[str] = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # File Storage
    upload_dir: str = Field(default="uploads", env="UPLOAD_DIR")
    max_file_size: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    allowed_file_types: str = Field(
        default="pdf,jpg,jpeg,png,doc,docx,txt",
        env="ALLOWED_FILE_TYPES"
    )
    
    # Audit and Compliance
    audit_log_retention_days: int = Field(default=2555, env="AUDIT_LOG_RETENTION_DAYS")  # 7 years for HIPAA
    enable_detailed_logging: bool = Field(default=True, env="ENABLE_DETAILED_LOGGING")
    
    # Session Management
    session_timeout_minutes: int = Field(default=480, env="SESSION_TIMEOUT_MINUTES")  # 8 hours
    max_failed_login_attempts: int = Field(default=5, env="MAX_FAILED_LOGIN_ATTEMPTS")
    account_lockout_minutes: int = Field(default=30, env="ACCOUNT_LOCKOUT_MINUTES")
    
    # Appointment Settings
    default_appointment_duration: int = Field(default=30, env="DEFAULT_APPOINTMENT_DURATION")  # minutes
    max_appointments_per_day: int = Field(default=50, env="MAX_APPOINTMENTS_PER_DAY")
    appointment_reminder_hours: str = Field(default="24,2", env="APPOINTMENT_REMINDER_HOURS")
    
    # WhatsApp Chatbot Settings
    chatbot_enabled: bool = Field(default=True, env="CHATBOT_ENABLED")
    chatbot_language: str = Field(default="en", env="CHATBOT_LANGUAGE")
    chatbot_session_timeout_minutes: int = Field(default=30, env="CHATBOT_SESSION_TIMEOUT_MINUTES")
    
    # Notification Settings
    enable_email_notifications: bool = Field(default=True, env="ENABLE_EMAIL_NOTIFICATIONS")
    enable_whatsapp_notifications: bool = Field(default=True, env="ENABLE_WHATSAPP_NOTIFICATIONS")
    enable_sms_notifications: bool = Field(default=False, env="ENABLE_SMS_NOTIFICATIONS")
    
    # Clinic Information
    clinic_name: str = Field(default="Dr. Dhingra's Clinic", env="CLINIC_NAME")
    clinic_address: Optional[str] = Field(default=None, env="CLINIC_ADDRESS")
    clinic_phone: Optional[str] = Field(default=None, env="CLINIC_PHONE")
    clinic_email: Optional[str] = Field(default=None, env="CLINIC_EMAIL")
    clinic_website: Optional[str] = Field(default=None, env="CLINIC_WEBSITE")
    clinic_timezone: str = Field(default="UTC", env="CLINIC_TIMEZONE")
    
    # Feature Flags
    enable_mfa: bool = Field(default=True, env="ENABLE_MFA")
    enable_calendar_integration: bool = Field(default=True, env="ENABLE_CALENDAR_INTEGRATION")
    enable_whatsapp_booking: bool = Field(default=True, env="ENABLE_WHATSAPP_BOOKING")
    enable_prescription_sharing: bool = Field(default=True, env="ENABLE_PRESCRIPTION_SHARING")
    enable_bulk_messaging: bool = Field(default=True, env="ENABLE_BULK_MESSAGING")
    
    # API Keys for External Services
    google_maps_api_key: Optional[str] = Field(default=None, env="GOOGLE_MAPS_API_KEY")
    twilio_account_sid: Optional[str] = Field(default=None, env="TWILIO_ACCOUNT_SID")
    twilio_auth_token: Optional[str] = Field(default=None, env="TWILIO_AUTH_TOKEN")
    twilio_phone_number: Optional[str] = Field(default=None, env="TWILIO_PHONE_NUMBER")
    
    # Advanced Security
    password_min_length: int = Field(default=8, env="PASSWORD_MIN_LENGTH")
    password_require_uppercase: bool = Field(default=True, env="PASSWORD_REQUIRE_UPPERCASE")
    password_require_lowercase: bool = Field(default=True, env="PASSWORD_REQUIRE_LOWERCASE")
    password_require_numbers: bool = Field(default=True, env="PASSWORD_REQUIRE_NUMBERS")
    password_require_special: bool = Field(default=True, env="PASSWORD_REQUIRE_SPECIAL")
    
    # HIPAA Compliance
    hipaa_compliant_mode: bool = Field(default=True, env="HIPAA_COMPLIANT_MODE")
    encrypt_patient_data: bool = Field(default=True, env="ENCRYPT_PATIENT_DATA")
    require_audit_logs: bool = Field(default=True, env="REQUIRE_AUDIT_LOGS")
    minimum_password_age_days: int = Field(default=1, env="MINIMUM_PASSWORD_AGE_DAYS")
    maximum_password_age_days: int = Field(default=90, env="MAXIMUM_PASSWORD_AGE_DAYS")
    
    # Backup and Recovery
    backup_enabled: bool = Field(default=True, env="BACKUP_ENABLED")
    backup_schedule: str = Field(default="0 2 * * *", env="BACKUP_SCHEDULE")  # Daily at 2 AM
    backup_retention_days: int = Field(default=30, env="BACKUP_RETENTION_DAYS")
    
    # Monitoring and Alerts
    enable_health_checks: bool = Field(default=True, env="ENABLE_HEALTH_CHECKS")
    alert_email: Optional[str] = Field(default=None, env="ALERT_EMAIL")
    enable_performance_monitoring: bool = Field(default=True, env="ENABLE_PERFORMANCE_MONITORING")
    
    class Config:
        # Accept unknown env vars to avoid extra_forbidden during Settings load
        extra = "allow"
        env_file = ".env"
        case_sensitive = False
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            # Handle empty string case
            if not v.strip():
                return "http://localhost:3000,http://localhost:8000"
            return v
        return v
    
    @field_validator("allowed_file_types", mode="before") 
    @classmethod
    def parse_allowed_file_types(cls, v):
        if isinstance(v, str):
            return v
        return v
    
    @field_validator("appointment_reminder_hours", mode="before")
    @classmethod
    def parse_reminder_hours(cls, v):
        if isinstance(v, str):
            return v
        return v
    
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL is required")
        if not v.startswith(("postgresql://", "postgresql+psycopg2://", "sqlite:///")):
            raise ValueError("DATABASE_URL must be a valid PostgreSQL or SQLite URL")
        return v
    
    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v):
        if not v or len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key(cls, v):
        if not v or len(v) < 32:
            raise ValueError("ENCRYPTION_KEY must be at least 32 characters long")
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
    
    @property
    def cors_origins_list(self) -> list:
        """Get CORS origins as a list"""
        if not self.cors_origins.strip():
            return ["http://localhost:3000", "http://localhost:8000"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    @property
    def allowed_file_types_list(self) -> list:
        """Get allowed file types as a list"""
        return [file_type.strip().lower() for file_type in self.allowed_file_types.split(",") if file_type.strip()]
    
    @property
    def appointment_reminder_hours_list(self) -> list:
        """Get appointment reminder hours as a list of integers"""
        return [int(hour.strip()) for hour in self.appointment_reminder_hours.split(",") if hour.strip()]

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

# Example environment variables for reference
ENV_EXAMPLE = """
# =================================
# Dr. Dhingra's Clinic Configuration
# =================================

# Environment
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=postgresql://username:password@localhost:5432/clinic_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Security
SECRET_KEY=your-super-secret-key-at-least-32-characters-long
ENCRYPTION_KEY=your-encryption-key-at-least-32-characters-long
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Origins (comma separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,https://yourdomain.com

# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_VERIFY_TOKEN=your_verify_token
WHATSAPP_WEBHOOK_URL=https://yourdomain.com/api/v1/whatsapp/webhook
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id

# Email - SendGrid
SENDGRID_API_KEY=your_sendgrid_api_key
SENDGRID_FROM_EMAIL=noreply@yourclinic.com

# Email - SMTP Alternative
# SMTP_SERVER=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USERNAME=your_email@gmail.com
# SMTP_PASSWORD=your_app_password
# SMTP_USE_TLS=true

# Google Calendar
GOOGLE_CALENDAR_CREDENTIALS_FILE=credentials.json
GOOGLE_CALENDAR_TOKEN_FILE=token.json
GOOGLE_CALENDAR_ID=primary

# Redis (Optional)
REDIS_URL=redis://localhost:6379
# REDIS_PASSWORD=your_redis_password

# File Storage
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760
ALLOWED_FILE_TYPES=pdf,jpg,jpeg,png,doc,docx,txt

# Clinic Information
CLINIC_NAME=Dr. Dhingra's Clinic
CLINIC_ADDRESS=123 Medical Street, Healthcare City, HC 12345
CLINIC_PHONE=+1-555-123-4567
CLINIC_EMAIL=info@drdhingraclinic.com
CLINIC_WEBSITE=https://drdhingraclinic.com
CLINIC_TIMEZONE=America/New_York

# Feature Flags
ENABLE_MFA=true
ENABLE_CALENDAR_INTEGRATION=true
ENABLE_WHATSAPP_BOOKING=true
ENABLE_PRESCRIPTION_SHARING=true
ENABLE_BULK_MESSAGING=true

# HIPAA Compliance
HIPAA_COMPLIANT_MODE=true
ENCRYPT_PATIENT_DATA=true
REQUIRE_AUDIT_LOGS=true
AUDIT_LOG_RETENTION_DAYS=2555

# Security
MAX_FAILED_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_MINUTES=30
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_NUMBERS=true
PASSWORD_REQUIRE_SPECIAL=true

# Notifications
ENABLE_EMAIL_NOTIFICATIONS=true
ENABLE_WHATSAPP_NOTIFICATIONS=true
ENABLE_SMS_NOTIFICATIONS=false

# Optional: Twilio for SMS
# TWILIO_ACCOUNT_SID=your_twilio_account_sid
# TWILIO_AUTH_TOKEN=your_twilio_auth_token
# TWILIO_PHONE_NUMBER=your_twilio_phone_number

# Optional: Google Maps
# GOOGLE_MAPS_API_KEY=your_google_maps_api_key

# Monitoring
ENABLE_HEALTH_CHECKS=true
ALERT_EMAIL=admin@drdhingraclinic.com
ENABLE_PERFORMANCE_MONITORING=true
"""

if __name__ == "__main__":
    # Generate example .env file
    with open(".env.example", "w") as f:
        f.write(ENV_EXAMPLE)
    print("Generated .env.example file")
    
    # Test configuration loading
    try:
        settings = get_settings()
        print(f"Configuration loaded successfully!")
        print(f"App: {settings.app_name} v{settings.app_version}")
        print(f"Environment: {settings.environment}")
        print(f"WhatsApp enabled: {settings.whatsapp_enabled}")
        print(f"Email enabled: {settings.email_enabled}")
        print(f"Calendar enabled: {settings.calendar_enabled}")
    except Exception as e:
        print(f"Configuration error: {e}")