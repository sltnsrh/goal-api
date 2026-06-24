from typing import Optional
import uuid
from sqlalchemy.orm import Session
from app.db.models import GoalEntity
from app.schemas import (
    AnalysisStatus,
    GoalAnalyzeRequest,
    GoalAnalyzeResponse,
    GoalCreateRequest,
    GoalDetailResponse,
    GoalPlanRequest,
    GoalPlanResponse,
    GoalUpdateRequest,
)
from app.repositories.goal_repository import create_goal, get_goal_by_id, list_goals, save_analysis, update_goal as update_goal_in_repository
from app.services.goal_analyzer import analyze_goal
from app.services.goal_planner import generate_plan


class GoalPlanNotReadyError(ValueError):
    pass


class GoalPlanGenerationError(ValueError):
    pass


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


def list_goals_with_pagination(db: Session, limit: int, offset: int) -> tuple[list[GoalEntity], int]:
    return list_goals(db, limit, offset)


def build_goal_detail_response(goal: GoalEntity) -> GoalDetailResponse:
    analysis = None
    analysis_status = AnalysisStatus.not_analyzed

    if goal.analysis_json:
        try:
            analysis = GoalAnalyzeResponse.model_validate_json(goal.analysis_json)
            analysis_status = AnalysisStatus.analyzed
        except Exception as exc:  # pragma: no cover - defensive guard for corrupted storage
            raise ValueError("Stored goal analysis is invalid") from exc

    return GoalDetailResponse(
        id=goal.id,
        goal=goal.goal,
        deadline_months=goal.deadline_months,
        weekly_hours=goal.weekly_hours,
        current_level=goal.current_level,
        analysis_status=analysis_status,
        analysis=analysis,
    )


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


def _build_goal_plan_request(goal: GoalEntity) -> GoalPlanRequest:
    if not goal.analysis_json:
        raise GoalPlanNotReadyError("Goal must be analyzed before planning")

    analysis = GoalAnalyzeResponse.model_validate_json(goal.analysis_json)
    if not analysis.feasible:
        raise GoalPlanNotReadyError("Goal analysis indicates the goal is not feasible")

    return GoalPlanRequest(
        goal=goal.goal,
        deadline_months=goal.deadline_months,
        weekly_hours=goal.weekly_hours,
        current_level=goal.current_level,
        analysis=analysis,
    )


def generate_goal_plan(goal: GoalEntity) -> GoalPlanResponse:
    request = _build_goal_plan_request(goal)
    try:
        return generate_plan(request)
    except ValueError as exc:
        raise GoalPlanGenerationError("Failed to parse generated plan response") from exc
