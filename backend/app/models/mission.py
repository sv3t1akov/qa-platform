"""
Mission-related models
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, ARRAY, Boolean
from sqlalchemy.dialects.postgresql import UUID, INET, ENUM
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.session import Base
import enum


class MissionStatus(str, enum.Enum):
    locked = "locked"
    available = "available"
    in_progress = "in_progress"
    completed = "completed"


class Difficulty(str, enum.Enum):
    Beginner = "Beginner"
    Intermediate = "Intermediate"
    Advanced = "Advanced"
    Expert = "Expert"


class BugDifficulty(str, enum.Enum):
    Easy = "Easy"
    Medium = "Medium"
    Hard = "Hard"


class Domain(Base):
    __tablename__ = "domains"

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    icon = Column(String(10), nullable=True)
    description = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    
    # Relationships
    missions = relationship("Mission", back_populates="domain", cascade="all, delete-orphan")


class Mission(Base):
    __tablename__ = "missions"

    id = Column(String(100), primary_key=True)
    domain_id = Column(String(50), ForeignKey("domains.id"), nullable=False)
    tier = Column(String(5), nullable=False)  # T1, T2, T3, T4, T5
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    difficulty = Column(String(20), nullable=True)
    estimated_time = Column(String(50), nullable=True)
    points = Column(Integer, default=0, nullable=False)
    bugs = Column(Integer, default=0, nullable=False)
    endpoint = Column(String(255), nullable=True)
    base_url = Column(String(255), nullable=True)
    theory_title = Column(String(200), nullable=True)
    theory_content = Column(Text, nullable=True)
    hints = Column(ARRAY(Text), nullable=True)
    task_description = Column(Text, nullable=True)
    request_body_example = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)  # Бизнес-правила для T3 миссий
    sort_order = Column(Integer, default=0, nullable=False)
    
    # Relationships
    domain = relationship("Domain", back_populates="missions")
    bugs_list = relationship("Bug", back_populates="mission", cascade="all, delete-orphan")
    user_progress = relationship("UserMissionProgress", back_populates="mission", cascade="all, delete-orphan")


class Bug(Base):
    __tablename__ = "bugs"

    id = Column(String(100), primary_key=True)
    mission_id = Column(String(100), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    flag = Column(String(100), unique=True, nullable=False)
    points = Column(Integer, default=0, nullable=False)
    difficulty = Column(String(20), nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    active = Column(Boolean, default=True, nullable=False)  # Phase2: false = dropped (not counted)
    
    # Relationships
    mission = relationship("Mission", back_populates="bugs_list")
    user_found_flags = relationship("UserFoundFlag", back_populates="bug", cascade="all, delete-orphan")


class UserMissionProgress(Base):
    __tablename__ = "user_mission_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    mission_id = Column(String(100), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False)
    # Используем существующий тип mission_status из PostgreSQL схемы
    status = Column(
        ENUM(MissionStatus, name='mission_status', create_type=False),
        default=MissionStatus.available,
        nullable=False
    )
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="mission_progress")
    mission = relationship("Mission", back_populates="user_progress")
    
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


class UserFoundFlag(Base):
    __tablename__ = "user_found_flags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    bug_id = Column(String(100), ForeignKey("bugs.id", ondelete="CASCADE"), nullable=False)
    found_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="found_flags")
    bug = relationship("Bug", back_populates="user_found_flags")
    
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    refresh_token_hash = Column(String(255), nullable=False, index=True)
    user_agent = Column(Text, nullable=True)
    ip_address = Column(INET, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
