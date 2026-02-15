"""
Rank model
"""
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship

from app.db.session import Base


class Rank(Base):
    __tablename__ = "ranks"

    id = Column(String(50), primary_key=True)
    name_ru = Column(String(100), nullable=False)
    name_en = Column(String(100), nullable=False)
    min_points = Column(Integer, nullable=False)
    color = Column(String(7), nullable=False)  # HEX color like #9CA3AF
    sort_order = Column(Integer, nullable=False)
    
    # Relationships
    # Опционально: если используем кэширование current_rank_id в users
    # users = relationship("User", back_populates="current_rank")
