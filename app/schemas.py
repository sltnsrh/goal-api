from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class AnalysisStatus(str, Enum):
    not_analyzed = "not_analyzed"
    analyzed = "analyzed"


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


class GoalListResponse(BaseModel):
    items: list[GoalResponse]
    total: int
    limit: int
    offset: int

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


class GoalDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    goal: str
    deadline_months: int
    weekly_hours: int
    current_level: str
    analysis_status: AnalysisStatus
    analysis_updated_at: datetime | None = None
    analysis: GoalAnalyzeResponse | None = None


class GoalPlanRequest(BaseModel):
    goal: str = Field(min_length=5, max_length=500)
    deadline_months: int = Field(gt=0, le=120)
    weekly_hours: int = Field(gt=0, le=168)
    current_level: str = Field(min_length=3, max_length=500)
    analysis: GoalAnalyzeResponse | None = None


class GoalPlanResponse(BaseModel):
    current_phase: str
    milestones: list[Milestone]
    next_week_tasks: list[str]


class GoalUpdateRequest(BaseModel):
    goal: str | None = Field(default=None, min_length=5, max_length=500)
    deadline_months: int | None = Field(default=None, gt=0, le=120)
    weekly_hours: int | None = Field(default=None, gt=0, le=168)
    current_level: str | None = Field(default=None, min_length=3, max_length=500)

    @model_validator(mode="after")
    def validate_update_payload(self) -> "GoalUpdateRequest":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")

        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")

        return self
