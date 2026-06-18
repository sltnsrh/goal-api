import uuid
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.database import Base

class GoalEntity(Base):
    __tablename__ = "goals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    goal = Column(String(500), nullable=False)
    deadline_months = Column(Integer, nullable=False)
    weekly_hours = Column(Integer, nullable=False)
    current_level = Column(String(500), nullable=False)
    analysis_json = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())