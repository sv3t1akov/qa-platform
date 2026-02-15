"""
User model
"""
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID, INET, ENUM
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.session import Base
import enum


class UserRole(str, enum.Enum):
    student = "student"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # NULL для OAuth пользователей
    # Используем существующий тип user_role из PostgreSQL схемы
    role = Column(
        ENUM(UserRole, name='user_role', create_type=False),
        default=UserRole.student,
        nullable=False
    )
    
    # OAuth данные
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    
    # Профиль
    display_name = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # Метаданные
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Для восстановления пароля
    reset_token = Column(String(255), nullable=True)
    reset_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Email верификация
    email_verified = Column(String(10), default='false', nullable=False)  # 'true' или 'false' как строка для совместимости
    verification_token = Column(String(255), nullable=True)
    verification_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    mission_progress = relationship("UserMissionProgress", back_populates="user", cascade="all, delete-orphan")
    found_flags = relationship("UserFoundFlag", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
