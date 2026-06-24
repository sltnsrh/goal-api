import uuid
from typing import Optional
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
from app.repositories import goal_repository
from app.services import goal_analyzer, goal_planner


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
    return goal_repository.create_goal(db, entity)


def get_goal(db: Session, goal_id: str) -> Optional[GoalEntity]:
    return goal_repository.get_goal_by_id(db, goal_id)


def list_goals_with_pagination(db: Session, limit: int, offset: int) -> tuple[list[GoalEntity], int]:
    return goal_repository.list_goals(db, limit, offset)


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
        goal=goal.goal,
        deadline_months=goal.deadline_months,
        weekly_hours=goal.weekly_hours,
        current_level=goal.current_level,
    )

    analysis = goal_analyzer.analyze_goal(request)
    goal_repository.save_analysis(db, goal, analysis.model_dump_json())
    return analysis


def update_goal(db: Session, goal_id: str, request: GoalUpdateRequest) -> Optional[GoalEntity]:
    update_data = request.model_dump(exclude_unset=True)
    return goal_repository.update_goal(db, goal_id, update_data)


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
        return goal_planner.generate_plan(request)
    except ValueError as exc:
        raise GoalPlanGenerationError("Failed to parse generated plan response") from exc
