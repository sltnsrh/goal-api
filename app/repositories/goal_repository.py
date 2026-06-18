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


def save_analysis(db: Session, goal: GoalEntity, analysis_json: str) -> GoalEntity:
    goal.analysis_json = analysis_json #type: ignore
    db.commit()
    db.refresh(goal)
    return goal
