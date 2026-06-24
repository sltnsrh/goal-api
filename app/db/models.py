import uuid
from sqlalchemy import Column, DateTime, Integer, String, Text, text
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
    analysis_status = Column(String(20), nullable=False, default="not_analyzed", server_default=text("'not_analyzed'"))
    analysis_updated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
