from datetime import date
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class Milestone(BaseModel):
    title: str
    start_date: date
    end_date: date
    total_hours: int

class GoalCreateRequest(BaseModel):
    goal: str = Field(min_length=5, max_length=500)
    deadline_months: int = Field(gt=0, le=120)
    weekly_hours: int = Field(gt=0, le=168)
    current_level: str = Field(min_length=3, max_length=500)

class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    goal: str
    deadline_months: int
    weekly_hours: int
    current_level: str

class GoalAnalyzeRequest(BaseModel):
    goal: str = Field(min_length=5, max_length=500)
    deadline_months: int = Field(gt=0, le=120)
    weekly_hours: int = Field(gt=0, le=168)
    current_level: str = Field(min_length=3, max_length=500)

class GoalAnalyzeResponse(BaseModel):
    clarified_goal: str
    feasible: bool
    risk_level: RiskLevel
    main_risks: list[str]
    missing_inputs: list[str]
    recommendation: str
    first_action: str

class GoalPlanRequest(BaseModel):
    goal: str = Field(min_length=5, max_length=500)
    deadline_months: int = Field(gt=0, le=120)
    weekly_hours: int = Field(gt=0, le=168)
    current_level: str = Field(min_length=3, max_length=500)
    analysis: Optional[GoalAnalyzeResponse] = None

class GoalPlanResponse(BaseModel):
    current_phase: str
    milestones: list[Milestone]
    next_week_tasks: list[str]