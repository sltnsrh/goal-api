from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.db.database import Base, get_db
from app.db import models  # noqa: F401
from app.main import app
from app.schemas import GoalAnalyzeResponse, GoalPlanResponse, Milestone, RiskLevel

_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def _get_test_db():
    db = _TestSession()
    try:
        yield db
    finally:
        db.close()


Base.metadata.create_all(bind=_engine)
app.dependency_overrides[get_db] = _get_test_db
client = TestClient(app)

_VALID_PAYLOAD = {
    "goal": "Run a half marathon",
    "deadline_months": 6,
    "weekly_hours": 5,
    "current_level": "Can run 5km comfortably",
}

_MOCK_ANALYSIS = GoalAnalyzeResponse(
    clarified_goal="Complete a half marathon in 6 months",
    feasible=True,
    risk_level=RiskLevel.medium,
    main_risks=["Injury risk", "Inconsistent training"],
    missing_inputs=[],
    recommendation="Follow a structured training plan",
    first_action="Register for a local race",
)

_MOCK_UNFEASIBLE_ANALYSIS = GoalAnalyzeResponse(
    clarified_goal="Complete a half marathon in 1 month",
    feasible=False,
    risk_level=RiskLevel.high,
    main_risks=["Insufficient time", "Injury risk"],
    missing_inputs=[],
    recommendation="Extend the deadline or reduce scope",
    first_action="Reassess the timeline",
)

_MOCK_PLAN = GoalPlanResponse(
    current_phase="Foundations",
    milestones=[
        Milestone(
            title="Ship first API",
            start_date=date(2026, 6, 22),
            end_date=date(2026, 8, 22),
            total_hours=64,
        )
    ],
    next_week_tasks=[
        "Set up project repo",
        "Define API schema",
        "Write first endpoint",
    ],
)


# ============================================================================
# POST /goals
# ============================================================================

def test_create_goal_returns_201():
    response = client.post("/goals", json=_VALID_PAYLOAD)
    assert response.status_code == 201


def test_create_goal_returns_id_and_location_header():
    response = client.post("/goals", json=_VALID_PAYLOAD)
    data = response.json()
    assert "id" in data
    assert response.headers["location"] == f"/goals/{data['id']}"


def test_create_goal_returns_correct_fields():
    response = client.post("/goals", json=_VALID_PAYLOAD)
    data = response.json()
    assert data["goal"] == _VALID_PAYLOAD["goal"]
    assert data["deadline_months"] == _VALID_PAYLOAD["deadline_months"]
    assert data["weekly_hours"] == _VALID_PAYLOAD["weekly_hours"]
    assert data["current_level"] == _VALID_PAYLOAD["current_level"]


def test_create_goal_validation_fails_on_short_goal():
    response = client.post("/goals", json={**_VALID_PAYLOAD, "goal": "ab"})
    assert response.status_code == 422


# ============================================================================
# GET /goals
# ============================================================================

def test_list_goals_returns_paginated_items():
    client.post("/goals", json=_VALID_PAYLOAD)
    client.post(
        "/goals",
        json={**_VALID_PAYLOAD, "goal": "Learn FastAPI deeply"},
    )

    response = client.get("/goals", params={"limit": 1, "offset": 0})

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert data["limit"] == 1
    assert data["offset"] == 0
    assert len(data["items"]) == 1
    assert "id" in data["items"][0]
    assert "goal" in data["items"][0]


def test_list_goals_returns_next_page():
    client.post("/goals", json=_VALID_PAYLOAD)
    client.post(
        "/goals",
        json={**_VALID_PAYLOAD, "goal": "Learn FastAPI deeply"},
    )

    response = client.get("/goals", params={"limit": 1, "offset": 1})

    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 1
    assert data["offset"] == 1
    assert len(data["items"]) == 1


# ============================================================================
# GET /goals/{goal_id}
# ============================================================================

def test_get_goal_returns_200():
    goal_id = client.post("/goals", json=_VALID_PAYLOAD).json()["id"]
    response = client.get(f"/goals/{goal_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == goal_id
    assert data["analysis_status"] == "not_analyzed"
    assert data["analysis_updated_at"] is None
    assert data["analysis"] is None


def test_get_goal_returns_404_for_unknown_id():
    response = client.get("/goals/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "GOAL_NOT_FOUND"


# ============================================================================
# POST /goals/{goal_id}/analyze
# ============================================================================

@patch("app.services.goal_service.goal_analyzer.analyze_goal")
def test_analyze_saved_goal_returns_200(mock_analyze):
    mock_analyze.return_value = _MOCK_ANALYSIS
    goal_id = client.post("/goals", json=_VALID_PAYLOAD).json()["id"]
    response = client.post(f"/goals/{goal_id}/analyze")
    assert response.status_code == 200
    data = response.json()
    assert data["feasible"] is True
    assert data["risk_level"] == "medium"


@patch("app.services.goal_service.goal_analyzer.analyze_goal")
def test_analyze_saved_goal_persists_analysis(mock_analyze):
    mock_analyze.return_value = _MOCK_ANALYSIS
    goal_id = client.post("/goals", json=_VALID_PAYLOAD).json()["id"]
    client.post(f"/goals/{goal_id}/analyze")
    db = _TestSession()
    entity = db.query(models.GoalEntity).filter(models.GoalEntity.id == goal_id).first()
    db.close()
    assert entity.analysis_json is not None


@patch("app.services.goal_service.goal_analyzer.analyze_goal")
def test_get_goal_returns_analysis_after_analyze(mock_analyze):
    mock_analyze.return_value = _MOCK_ANALYSIS
    goal_id = client.post("/goals", json=_VALID_PAYLOAD).json()["id"]

    analyze_response = client.post(f"/goals/{goal_id}/analyze")
    assert analyze_response.status_code == 200

    response = client.get(f"/goals/{goal_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["analysis_status"] == "analyzed"
    assert data["analysis_updated_at"] is not None
    assert data["analysis"]["feasible"] is True
    assert data["analysis"]["risk_level"] == "medium"
    assert data["analysis"]["clarified_goal"] == _MOCK_ANALYSIS.clarified_goal


def test_analyze_goal_returns_404_for_unknown_id():
    response = client.post("/goals/00000000-0000-0000-0000-000000000000/analyze")
    assert response.status_code == 404


@patch("app.services.goal_service.goal_analyzer.analyze_goal")
def test_analyze_goal_returns_502_on_ai_error(mock_analyze):
    mock_analyze.side_effect = ValueError("OpenAI timeout")
    goal_id = client.post("/goals", json=_VALID_PAYLOAD).json()["id"]
    response = client.post(f"/goals/{goal_id}/analyze")
    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "AI_PROVIDER_ERROR"


# ============================================================================
# POST /goals/{goal_id}/plan
# ============================================================================


def test_plan_goal_returns_404_for_unknown_id():
    response = client.post("/goals/00000000-0000-0000-0000-000000000000/plan")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "GOAL_NOT_FOUND"


def test_plan_goal_returns_409_when_not_analyzed():
    goal_id = client.post("/goals", json=_VALID_PAYLOAD).json()["id"]
    response = client.post(f"/goals/{goal_id}/plan")
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "GOAL_PLAN_NOT_READY"


@patch("app.services.goal_service.goal_analyzer.analyze_goal")
def test_plan_goal_returns_409_when_goal_is_not_feasible(mock_analyze):
    mock_analyze.return_value = _MOCK_UNFEASIBLE_ANALYSIS
    goal_id = client.post("/goals", json=_VALID_PAYLOAD).json()["id"]
    client.post(f"/goals/{goal_id}/analyze")

    response = client.post(f"/goals/{goal_id}/plan")

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "GOAL_PLAN_NOT_READY"


@patch("app.services.goal_service.goal_planner.generate_plan")
@patch("app.services.goal_service.goal_analyzer.analyze_goal")
def test_plan_goal_returns_200_with_analysis_and_plan(mock_analyze, mock_generate_plan):
    mock_analyze.return_value = _MOCK_ANALYSIS
    mock_generate_plan.return_value = _MOCK_PLAN

    goal_id = client.post("/goals", json=_VALID_PAYLOAD).json()["id"]
    client.post(f"/goals/{goal_id}/analyze")

    response = client.post(f"/goals/{goal_id}/plan")

    assert response.status_code == 200
    data = response.json()
    assert data["current_phase"] == _MOCK_PLAN.current_phase
    assert len(data["milestones"]) == 1
    assert data["milestones"][0]["title"] == _MOCK_PLAN.milestones[0].title
    assert data["next_week_tasks"] == _MOCK_PLAN.next_week_tasks


_UPDATE_PAYLOAD = {
    "goal": "Run a full marathon",
    "weekly_hours": 7,
}

def test_patch_goal_returns_200_and_updates_fields():
    goal_id = client.post("/goals", json=_VALID_PAYLOAD).json()["id"]

    response = client.patch(f"/goals/{goal_id}", json=_UPDATE_PAYLOAD)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == goal_id
    assert data["goal"] == _UPDATE_PAYLOAD["goal"]
    assert data["weekly_hours"] == _UPDATE_PAYLOAD["weekly_hours"]
    assert data["deadline_months"] == _VALID_PAYLOAD["deadline_months"]
    assert data["current_level"] == _VALID_PAYLOAD["current_level"]

def test_patch_goal_returns_404_for_unknown_id():
    response = client.patch("/goals/00000000-0000-0000-0000-000000000000", json=_UPDATE_PAYLOAD)
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "GOAL_NOT_FOUND"

def test_patch_goal_returns_422_for_empty_body():
    goal_id = client.post("/goals", json=_VALID_PAYLOAD).json()["id"]
    response = client.patch(f"/goals/{goal_id}", json={})
    assert response.status_code == 422

def test_patch_goal_returns_422_for_invalid_values():
    goal_id = client.post("/goals", json=_VALID_PAYLOAD).json()["id"]
    response = client.patch(f"/goals/{goal_id}", json={"weekly_hours": 0})
    assert response.status_code == 422


@patch("app.services.goal_service.goal_analyzer.analyze_goal")
def test_patch_goal_clears_previous_analysis(mock_analyze):
    mock_analyze.return_value = _MOCK_ANALYSIS
    goal_id = client.post("/goals", json=_VALID_PAYLOAD).json()["id"]
    client.post(f"/goals/{goal_id}/analyze")

    response = client.patch(f"/goals/{goal_id}", json=_UPDATE_PAYLOAD)

    assert response.status_code == 200
    get_response = client.get(f"/goals/{goal_id}")
    assert get_response.status_code == 200
    assert get_response.json()["analysis_status"] == "not_analyzed"
    assert get_response.json()["analysis_updated_at"] is None
    assert get_response.json()["analysis"] is None
    db = _TestSession()
    entity = db.query(models.GoalEntity).filter(models.GoalEntity.id == goal_id).first()
    db.close()
    assert entity.analysis_json is None  # type: ignore[assignment] 
