from enum import Enum
from pydantic import BaseModel, Field

class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

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