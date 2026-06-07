import pytest
from datetime import date
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from app.main import app
from app.schemas import GoalAnalyzeResponse, GoalPlanRequest, GoalPlanResponse, RiskLevel
from app.services.goal_planner import _GoalPlanRaw, _MilestoneRaw, _build_user_prompt, generate_plan

client = TestClient(app)

_VALID_REQUEST = {
    "goal": "Become a stronger backend engineer",
    "deadline_months": 6,
    "weekly_hours": 8,
    "current_level": "Python intermediate",
}

_MOCK_RAW = _GoalPlanRaw(
    current_phase="Foundations",
    milestones=[
        _MilestoneRaw(
            title="Ship first API",
            start_date=date(2026, 6, 6),
            end_date=date(2026, 9, 6),
        ),
        _MilestoneRaw(
            title="Deploy to cloud",
            start_date=date(2026, 9, 7),
            end_date=date(2026, 12, 6),
        ),
    ],
    next_week_tasks=[
        "Set up project repo",
        "Define API schema",
        "Write first endpoint",
    ],
)


def _make_mock_parse(raw: _GoalPlanRaw = _MOCK_RAW) -> MagicMock:
    mock_response = MagicMock()
    mock_response.output_parsed = raw
    return mock_response


# ============================================================================
# PROMPT BUILDER TESTS
# ============================================================================

def test_build_user_prompt_without_analysis():
    request = GoalPlanRequest(**_VALID_REQUEST)
    prompt = _build_user_prompt(request)
    assert "Create a concrete execution plan." in prompt
    assert "Start date:" in prompt
    assert "Prior analysis: none" in prompt


def test_build_user_prompt_with_analysis():
    request = GoalPlanRequest(
        **_VALID_REQUEST,
        analysis=GoalAnalyzeResponse(
            clarified_goal="Become a stronger backend engineer",
            feasible=True,
            risk_level=RiskLevel.medium,
            main_risks=["Time pressure", "Scope creep"],
            missing_inputs=[],
            recommendation="Focus on one stack and ship small projects",
            first_action="Pick one backend project",
        ),
    )
    prompt = _build_user_prompt(request)
    assert "Start date:" in prompt
    assert "Prior analysis:\n- risk_level: medium" in prompt
    assert "- main_risks: Time pressure; Scope creep" in prompt
    assert "- recommendation: Focus on one stack and ship small projects" in prompt
    assert "Use 1 to 6 milestones." in prompt
    assert "start_date and end_date as ISO dates" in prompt
    assert "Keep next_week_tasks to 3 to 5 actions" in prompt
    assert "total_hours" not in prompt
    assert "<specific book>" not in prompt
    assert "Do not use placeholder text" in prompt


# ============================================================================
# VALIDATION TESTS
# ============================================================================

def test_plan_missing_goal_field():
    payload = {k: v for k, v in _VALID_REQUEST.items() if k != "goal"}
    assert client.post("/goals/plan", json=payload).status_code == 422


def test_plan_goal_too_short():
    assert client.post("/goals/plan", json={**_VALID_REQUEST, "goal": "ab"}).status_code == 422


def test_plan_goal_too_long():
    assert client.post("/goals/plan", json={**_VALID_REQUEST, "goal": "a" * 501}).status_code == 422


def test_plan_deadline_months_zero():
    assert client.post("/goals/plan", json={**_VALID_REQUEST, "deadline_months": 0}).status_code == 422


def test_plan_deadline_months_too_high():
    assert client.post("/goals/plan", json={**_VALID_REQUEST, "deadline_months": 121}).status_code == 422


def test_plan_weekly_hours_zero():
    assert client.post("/goals/plan", json={**_VALID_REQUEST, "weekly_hours": 0}).status_code == 422


def test_plan_weekly_hours_too_high():
    assert client.post("/goals/plan", json={**_VALID_REQUEST, "weekly_hours": 169}).status_code == 422


def test_plan_current_level_too_short():
    assert client.post("/goals/plan", json={**_VALID_REQUEST, "current_level": "ab"}).status_code == 422


# ============================================================================
# RESPONSE STRUCTURE TESTS
# ============================================================================

@patch("app.services.goal_planner.client.responses.parse")
def test_plan_response_structure(mock_parse):
    mock_parse.return_value = _make_mock_parse()
    response = client.post("/goals/plan", json=_VALID_REQUEST)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["current_phase"], str)
    assert isinstance(data["milestones"], list)
    assert isinstance(data["next_week_tasks"], list)
    milestone = data["milestones"][0]
    assert isinstance(milestone["title"], str)
    assert isinstance(milestone["start_date"], str)
    assert isinstance(milestone["end_date"], str)
    assert isinstance(milestone["total_hours"], int)


# ============================================================================
# HAPPY PATH TESTS
# ============================================================================

@patch("app.services.goal_planner.client.responses.parse")
def test_plan_happy_path_without_analysis(mock_parse):
    mock_parse.return_value = _make_mock_parse()
    response = client.post("/goals/plan", json=_VALID_REQUEST)
    assert response.status_code == 200
    data = response.json()
    assert data["current_phase"] == "Foundations"
    assert len(data["milestones"]) == 2
    assert len(data["next_week_tasks"]) == 3
    user_message = mock_parse.call_args.kwargs["input"][1]["content"]
    assert "Prior analysis: none" in user_message
    assert "Start date:" in user_message


@patch("app.services.goal_planner.client.responses.parse")
def test_plan_happy_path_with_analysis(mock_parse):
    mock_parse.return_value = _make_mock_parse()
    payload = {
        **_VALID_REQUEST,
        "analysis": {
            "clarified_goal": "Become a stronger backend engineer",
            "feasible": True,
            "risk_level": "medium",
            "main_risks": ["Time pressure", "Scope creep"],
            "missing_inputs": [],
            "recommendation": "Ship one project end to end",
            "first_action": "Pick a stack and commit",
        },
    }
    response = client.post("/goals/plan", json=payload)
    assert response.status_code == 200
    user_message = mock_parse.call_args.kwargs["input"][1]["content"]
    assert "risk_level: medium" in user_message
    assert "Time pressure" in user_message


@patch("app.services.goal_planner.client.responses.parse")
def test_plan_ai_provider_error_returns_502(mock_parse):
    mock_parse.side_effect = ValueError("OpenAI connection failed")
    response = client.post("/goals/plan", json=_VALID_REQUEST)
    assert response.status_code == 502
    detail = response.json()["detail"]
    assert detail["code"] == "AI_PROVIDER_ERROR"
    assert "OpenAI connection failed" in detail["message"]


def test_plan_returns_422_when_analysis_not_feasible():
    payload = {
        **_VALID_REQUEST,
        "analysis": {
            "clarified_goal": "Become a surgeon",
            "feasible": False,
            "risk_level": "high",
            "main_risks": ["Insufficient time", "No medical background"],
            "missing_inputs": [],
            "recommendation": "Extend timeline to at least 10 years",
            "first_action": "Research medical school prerequisites",
        },
    }
    response = client.post("/goals/plan", json=payload)
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "GOAL_NOT_FEASIBLE"
    assert "Extend timeline" in detail["message"]


@patch("app.services.goal_planner.client.responses.parse")
def test_plan_output_parsed_none_raises_value_error(mock_parse):
    mock_response = MagicMock()
    mock_response.output_parsed = None
    mock_parse.return_value = mock_response
    with pytest.raises(ValueError, match="Failed to parse generated plan response"):
        generate_plan(GoalPlanRequest(**_VALID_REQUEST))
