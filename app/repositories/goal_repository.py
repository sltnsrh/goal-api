from typing import Optional

from sqlalchemy.orm import Session
from app.db.models import GoalEntity


def create_goal(db: Session, entity: GoalEntity) -> GoalEntity:
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


def get_goal_by_id(db: Session, goal_id: str) -> Optional[GoalEntity]:
    return db.query(GoalEntity).filter(GoalEntity.id == goal_id).first()


def list_goals(db: Session, limit: int, offset: int) -> tuple[list[GoalEntity], int]:
    query = db.query(GoalEntity)
    total = query.count()
    items = (
        query.order_by(GoalEntity.created_at.desc(), GoalEntity.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return items, total


def save_analysis(db: Session, goal: GoalEntity, analysis_json: str) -> GoalEntity:
    goal.analysis_json = analysis_json  # type: ignore[assignment]
    db.commit()
    db.refresh(goal)
    return goal


def update_goal(db: Session, goal_id: str, update_data: dict[str, object]) -> Optional[GoalEntity]:
    goal = get_goal_by_id(db, goal_id)
    if goal is None:
        return None

    for field_name, value in update_data.items():
        setattr(goal, field_name, value)

    goal.analysis_json = None  # type: ignore[assignment]
    db.commit()
    db.refresh(goal)
    return goal
