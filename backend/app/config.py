"""
Application configuration using pydantic-settings
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = ""
    
    # JWT
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""
    
    # Email (для восстановления пароля)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    
    # App
    FRONTEND_URL: str = "https://qa-platform-frontend.fly.dev"
    LAB_BASE_URL: str = "https://qa-lab-{mission_id}.fly.dev"
    PLATFORM_SECRET: str = "platform-secret-key"
    
    # Debug
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        # Не валидировать обязательность полей при старте
        # Поля будут проверяться только при использовании
        validate_assignment = False


settings = Settings()
