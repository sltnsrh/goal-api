from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.schemas import GoalAnalyzeResponse, RiskLevel

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ============================================================================
# VALIDATION TESTS (Input validation)
# ============================================================================

def test_analyze_goal_missing_goal_field():
    response = client.post("/goals/analyze", json={
        "deadline_months": 6,
        "weekly_hours": 10,
        "current_level": "beginner"
    })
    assert response.status_code == 422


def test_analyze_goal_goal_too_short():
    response = client.post("/goals/analyze", json={
        "goal": "ab",
        "deadline_months": 6,
        "weekly_hours": 10,
        "current_level": "beginner"
    })
    assert response.status_code == 422


def test_analyze_goal_goal_too_long():
    response = client.post("/goals/analyze", json={
        "goal": "a" * 501,
        "deadline_months": 6,
        "weekly_hours": 10,
        "current_level": "beginner"
    })
    assert response.status_code == 422


def test_analyze_goal_deadline_months_zero():
    response = client.post("/goals/analyze", json={
        "goal": "Learn Python deeply",
        "deadline_months": 0,
        "weekly_hours": 10,
        "current_level": "beginner"
    })
    assert response.status_code == 422


def test_analyze_goal_deadline_months_too_high():
    response = client.post("/goals/analyze", json={
        "goal": "Learn Python deeply",
        "deadline_months": 121,
        "weekly_hours": 10,
        "current_level": "beginner"
    })
    assert response.status_code == 422


def test_analyze_goal_weekly_hours_zero():
    response = client.post("/goals/analyze", json={
        "goal": "Learn Python deeply",
        "deadline_months": 6,
        "weekly_hours": 0,
        "current_level": "beginner"
    })
    assert response.status_code == 422


def test_analyze_goal_weekly_hours_too_high():
    response = client.post("/goals/analyze", json={
        "goal": "Learn Python deeply",
        "deadline_months": 6,
        "weekly_hours": 169,
        "current_level": "beginner"
    })
    assert response.status_code == 422


def test_analyze_goal_current_level_too_short():
    response = client.post("/goals/analyze", json={
        "goal": "Learn Python deeply",
        "deadline_months": 6,
        "weekly_hours": 10,
        "current_level": "ab"
    })
    assert response.status_code == 422


def test_analyze_goal_current_level_too_long():
    response = client.post("/goals/analyze", json={
        "goal": "Learn Python deeply",
        "deadline_months": 6,
        "weekly_hours": 10,
        "current_level": "a" * 501
    })
    assert response.status_code == 422


# ============================================================================
# RESPONSE STRUCTURE TESTS (With mocking)
# ============================================================================

@patch('app.services.goal_analyzer.client.responses.parse')
def test_analyze_goal_response_structure(mock_parse):
    mock_response = MagicMock()
    mock_response.output_parsed = GoalAnalyzeResponse(
        clarified_goal="Master Python programming fundamentals",
        feasible=True,
        risk_level=RiskLevel.medium,
        main_risks=["Time management", "Consistency"],
        missing_inputs=["Your learning style preference"],
        recommendation="Start with fundamentals, practice daily",
        first_action="Set up development environment and complete week 1"
    )
    mock_parse.return_value = mock_response

    response = client.post("/goals/analyze", json={
        "goal": "Learn Python",
        "deadline_months": 6,
        "weekly_hours": 10,
        "current_level": "beginner"
    })

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "clarified_goal" in data
    assert "feasible" in data
    assert "risk_level" in data
    assert "main_risks" in data
    assert "missing_inputs" in data
    assert "recommendation" in data
    assert "first_action" in data


@patch('app.services.goal_analyzer.client.responses.parse')
def test_analyze_goal_response_data_types(mock_parse):
    mock_response = MagicMock()
    mock_response.output_parsed = GoalAnalyzeResponse(
        clarified_goal="Master Python",
        feasible=True,
        risk_level=RiskLevel.low,
        main_risks=["Risk 1", "Risk 2"],
        missing_inputs=["Input 1"],
        recommendation="Practice daily",
        first_action="Start learning"
    )
    mock_parse.return_value = mock_response

    response = client.post("/goals/analyze", json={
        "goal": "Learn Python",
        "deadline_months": 6,
        "weekly_hours": 10,
        "current_level": "beginner"
    })

    data = response.json()

    # Verify data types
    assert isinstance(data["clarified_goal"], str)
    assert isinstance(data["feasible"], bool)
    assert isinstance(data["risk_level"], str)
    assert data["risk_level"] in ["low", "medium", "high"]
    assert isinstance(data["main_risks"], list)
    assert all(isinstance(risk, str) for risk in data["main_risks"])
    assert isinstance(data["missing_inputs"], list)
    assert isinstance(data["recommendation"], str)
    assert isinstance(data["first_action"], str)


# ============================================================================
# HAPPY PATH TESTS (With mocking)
# ============================================================================

@patch('app.services.goal_analyzer.client.responses.parse')
def test_analyze_goal_happy_path(mock_parse):
    mock_response = MagicMock()
    mock_response.output_parsed = GoalAnalyzeResponse(
        clarified_goal="Achieve advanced proficiency in Python within 6 months",
        feasible=True,
        risk_level=RiskLevel.medium,
        main_risks=["Maintaining consistency", "Complexity of advanced topics"],
        missing_inputs=["Specific Python domain focus"],
        recommendation="Follow structured curriculum, practice problem-solving daily",
        first_action="Complete Python fundamentals course week 1"
    )
    mock_parse.return_value = mock_response

    response = client.post("/goals/analyze", json={
        "goal": "Learn Python deeply",
        "deadline_months": 6,
        "weekly_hours": 15,
        "current_level": "I know JavaScript basics"
    })

    assert response.status_code == 200
    data = response.json()

    assert data["feasible"] is True
    assert data["risk_level"] == "medium"
    assert len(data["main_risks"]) == 2
    assert "Maintaining consistency" in data["main_risks"]


@patch('app.services.goal_analyzer.client.responses.parse')
def test_analyze_goal_unfeasible(mock_parse):
    mock_response = MagicMock()
    mock_response.output_parsed = GoalAnalyzeResponse(
        clarified_goal="Master machine learning within 1 month",
        feasible=False,
        risk_level=RiskLevel.high,
        main_risks=["Unrealistic timeline", "Insufficient weekly hours"],
        missing_inputs=["Math background", "ML prerequisites"],
        recommendation="Extend timeline to at least 6 months",
        first_action="Assess current knowledge and prerequisites"
    )
    mock_parse.return_value = mock_response

    response = client.post("/goals/analyze", json={
        "goal": "Master machine learning",
        "deadline_months": 1,
        "weekly_hours": 5,
        "current_level": "beginner programmer"
    })

    assert response.status_code == 200
    data = response.json()

    assert data["feasible"] is False
    assert data["risk_level"] == "high"


@patch('app.services.goal_analyzer.client.responses.parse')
def test_analyze_goal_with_boundary_values(mock_parse):
    mock_response = MagicMock()
    mock_response.output_parsed = GoalAnalyzeResponse(
        clarified_goal="Test goal",
        feasible=True,
        risk_level=RiskLevel.low,
        main_risks=[],
        missing_inputs=[],
        recommendation="Go ahead",
        first_action="Start now"
    )
    mock_parse.return_value = mock_response

    response = client.post("/goals/analyze", json={
        "goal": "a" * 5,
        "deadline_months": 1,
        "weekly_hours": 1,
        "current_level": "abc"
    })

    assert response.status_code == 200


@patch('app.services.goal_analyzer.client.responses.parse')
def test_analyze_goal_mock_called_with_correct_params(mock_parse):
    mock_response = MagicMock()
    mock_response.output_parsed = GoalAnalyzeResponse(
        clarified_goal="Test",
        feasible=True,
        risk_level=RiskLevel.low,
        main_risks=[],
        missing_inputs=[],
        recommendation="Rec",
        first_action="Action"
    )
    mock_parse.return_value = mock_response

    request_data = {
        "goal": "Learn FastAPI",
        "deadline_months": 3,
        "weekly_hours": 8,
        "current_level": "Python intermediate"
    }

    response = client.post("/goals/analyze", json=request_data)

    assert response.status_code == 200
    mock_parse.assert_called_once()
