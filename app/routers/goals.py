from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas import GoalAnalyzeResponse, GoalCreateRequest, GoalListResponse, GoalResponse, GoalUpdateRequest
from app.services.goal_service import analyze_saved_goal, create_new_goal, get_goal, list_goals_with_pagination, update_goal

router = APIRouter(prefix="/goals", tags=["goals"])

_NOT_FOUND = {"code": "GOAL_NOT_FOUND", "message": "Goal not found"}


@router.post("", response_model=GoalResponse, status_code=201)
def create_goal_endpoint(
    request: GoalCreateRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> GoalResponse:
    entity = create_new_goal(db, request)
    response.headers["Location"] = f"/goals/{entity.id}"
    return GoalResponse.model_validate(entity)


@router.get("", response_model=GoalListResponse)
def list_goals_endpoint(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> GoalListResponse:
    items, total = list_goals_with_pagination(db, limit, offset)
    return GoalListResponse(
        items=[GoalResponse.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{goal_id}", response_model=GoalResponse)
def get_goal_endpoint(goal_id: str, db: Session = Depends(get_db)) -> GoalResponse:
    entity = get_goal(db, goal_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=_NOT_FOUND)
    return GoalResponse.model_validate(entity)


@router.post("/{goal_id}/analyze", response_model=GoalAnalyzeResponse)
def analyze_goal_endpoint(goal_id: str, db: Session = Depends(get_db)) -> GoalAnalyzeResponse:
    entity = get_goal(db, goal_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=_NOT_FOUND)
    try:
        return analyze_saved_goal(db, entity)
    except (ValueError, OSError) as e:
        raise HTTPException(
            status_code=502,
            detail={"code": "AI_PROVIDER_ERROR", "message": str(e)},
        )
    
@router.patch("/{goal_id}", response_model=GoalResponse)
def update_goal_endpoint(
    goal_id: str,
    request: GoalUpdateRequest,
    db: Session = Depends(get_db),
) -> GoalResponse:
    entity = update_goal(db, goal_id, request)
    if entity is None:
        raise HTTPException(status_code=404, detail=_NOT_FOUND)
    return GoalResponse.model_validate(entity)
