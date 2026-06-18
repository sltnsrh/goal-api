from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas import GoalCreateRequest, GoalResponse, GoalAnalyzeResponse
from app.services.goal_service import analyze_saved_goal, create_new_goal, get_goal

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