from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas import (
    GoalAnalyzeResponse,
    GoalCreateRequest,
    GoalDetailResponse,
    GoalListResponse,
    GoalPlanResponse,
    GoalResponse,
    GoalUpdateRequest,
)
from app.services import goal_service

router = APIRouter(prefix="/goals", tags=["goals"])

_NOT_FOUND = {"code": "GOAL_NOT_FOUND", "message": "Goal not found"}
_PLAN_NOT_READY = {"code": "GOAL_PLAN_NOT_READY", "message": "Goal must be analyzed and feasible before planning"}


@router.post("", response_model=GoalResponse, status_code=201)
def create_goal(
    request: GoalCreateRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> GoalResponse:
    entity = goal_service.create_new_goal(db, request)
    response.headers["Location"] = f"/goals/{entity.id}"
    return GoalResponse.model_validate(entity)


@router.get("", response_model=GoalListResponse)
def list_goals(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> GoalListResponse:
    items, total = goal_service.list_goals_with_pagination(db, limit, offset)
    return GoalListResponse(
        items=[GoalResponse.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{goal_id}", response_model=GoalDetailResponse)
def get_goal(goal_id: str, db: Session = Depends(get_db)) -> GoalDetailResponse:
    entity = goal_service.get_goal(db, goal_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=_NOT_FOUND)
    return goal_service.build_goal_detail_response(entity)


@router.post("/{goal_id}/analyze", response_model=GoalAnalyzeResponse)
def analyze_goal(goal_id: str, db: Session = Depends(get_db)) -> GoalAnalyzeResponse:
    entity = goal_service.get_goal(db, goal_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=_NOT_FOUND)
    try:
        return goal_service.analyze_saved_goal(db, entity)
    except (ValueError, OSError) as e:
        raise HTTPException(
            status_code=502,
            detail={"code": "AI_PROVIDER_ERROR", "message": str(e)},
        )


@router.post("/{goal_id}/plan", response_model=GoalPlanResponse)
def plan_goal(goal_id: str, db: Session = Depends(get_db)) -> GoalPlanResponse:
    entity = goal_service.get_goal(db, goal_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=_NOT_FOUND)
    try:
        return goal_service.generate_goal_plan(entity)
    except goal_service.GoalPlanNotReadyError as e:
        raise HTTPException(status_code=409, detail={"code": _PLAN_NOT_READY["code"], "message": str(e)})
    except goal_service.GoalPlanGenerationError as e:
        raise HTTPException(
            status_code=502,
            detail={"code": "AI_PROVIDER_ERROR", "message": str(e)},
        )


@router.patch("/{goal_id}", response_model=GoalResponse)
def update_goal(
    goal_id: str,
    request: GoalUpdateRequest,
    db: Session = Depends(get_db),
) -> GoalResponse:
    entity = goal_service.update_goal(db, goal_id, request)
    if entity is None:
        raise HTTPException(status_code=404, detail=_NOT_FOUND)
    return GoalResponse.model_validate(entity)
