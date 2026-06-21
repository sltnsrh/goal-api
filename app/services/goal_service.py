from typing import Optional
import uuid
from sqlalchemy.orm import Session
from app.db.models import GoalEntity
from app.schemas import GoalAnalyzeRequest, GoalAnalyzeResponse, GoalCreateRequest, GoalUpdateRequest
from app.repositories.goal_repository import create_goal, get_goal_by_id, save_analysis, update_goal as update_goal_in_repository
from app.services.goal_analyzer import analyze_goal


def create_new_goal(db: Session, request: GoalCreateRequest) -> GoalEntity:
    entity = GoalEntity(
        id=str(uuid.uuid4()),
        goal=request.goal,
        deadline_months=request.deadline_months,
        weekly_hours=request.weekly_hours,
        current_level=request.current_level,
    )
    return create_goal(db, entity)


def get_goal(db: Session, goal_id: str) -> Optional[GoalEntity]:
    return get_goal_by_id(db, goal_id)


def analyze_saved_goal(db: Session, goal: GoalEntity) -> GoalAnalyzeResponse:
    request = GoalAnalyzeRequest(
        goal=goal.goal, # type: ignore
        deadline_months=goal.deadline_months, # type: ignore
        weekly_hours=goal.weekly_hours, # type: ignore
        current_level=goal.current_level, # type: ignore
    )

    analysis = analyze_goal(request)
    save_analysis(db, goal, analysis.model_dump_json())
    return analysis

def update_goal(db: Session, goal_id: str, request: GoalUpdateRequest) -> Optional[GoalEntity]:
    return update_goal_in_repository(db, goal_id, request)