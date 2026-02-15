"""
Pydantic схемы для авторизации
"""
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    student = "student"
    admin = "admin"


# Регистрация
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        from app.utils.validators import validate_password
        is_valid, error = validate_password(v)
        if not is_valid:
            raise ValueError(error)
        return v


class RegisterResponse(BaseModel):
    user_id: str
    email: str
    message: str = "Регистрация успешна"


# Логин
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # секунды


# Refresh
class RefreshRequest(BaseModel):
    refresh_token: str


# Забыли пароль
class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str = "Если email существует, инструкции отправлены"


# Сброс пароля
class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        from app.utils.validators import validate_password
        is_valid, error = validate_password(v)
        if not is_valid:
            raise ValueError(error)
        return v


# Email верификация
class VerifyEmailRequest(BaseModel):
    token: str


class VerifyEmailResponse(BaseModel):
    message: str = "Email успешно подтверждён"


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class ResendVerificationResponse(BaseModel):
    message: str = "Письмо с подтверждением отправлено"


# Пользователь
class UserResponse(BaseModel):
    id: str
    email: str
    role: UserRole
    display_name: Optional[str]
    avatar_url: Optional[str]
    email_verified: Optional[str] = 'false'
    created_at: datetime
    
    class Config:
        from_attributes = True
