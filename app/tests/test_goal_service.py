from unittest.mock import MagicMock, patch

from app.db.models import GoalEntity
from app.schemas import GoalAnalyzeResponse, GoalCreateRequest, RiskLevel
from app.services.goal_service import analyze_saved_goal, create_new_goal, get_goal


_CREATE_REQUEST = GoalCreateRequest(
    goal="Build a portfolio project",
    deadline_months=4,
    weekly_hours=8,
    current_level="Intermediate Python",
)


def test_create_new_goal_builds_entity_and_persists_it():
    db = MagicMock()
    expected_entity = GoalEntity(
        id="goal-123",
        goal=_CREATE_REQUEST.goal,
        deadline_months=_CREATE_REQUEST.deadline_months,
        weekly_hours=_CREATE_REQUEST.weekly_hours,
        current_level=_CREATE_REQUEST.current_level,
    )

    with patch("app.services.goal_service.uuid.uuid4", return_value="goal-123"), patch(
        "app.services.goal_service.create_goal", return_value=expected_entity
    ) as mock_create_goal:
        result = create_new_goal(db, _CREATE_REQUEST)

    assert result is expected_entity
    mock_create_goal.assert_called_once()
    created_entity = mock_create_goal.call_args.args[1]
    assert created_entity.id == "goal-123"
    assert created_entity.goal == _CREATE_REQUEST.goal
    assert created_entity.deadline_months == _CREATE_REQUEST.deadline_months
    assert created_entity.weekly_hours == _CREATE_REQUEST.weekly_hours
    assert created_entity.current_level == _CREATE_REQUEST.current_level


def test_get_goal_delegates_to_repository():
    db = MagicMock()
    expected_entity = MagicMock()

    with patch("app.services.goal_service.get_goal_by_id", return_value=expected_entity) as mock_get_goal:
        result = get_goal(db, "goal-123")

    assert result is expected_entity
    mock_get_goal.assert_called_once_with(db, "goal-123")


def test_analyze_saved_goal_builds_request_and_persists_analysis():
    db = MagicMock()
    goal = GoalEntity(
        id="goal-123",
        goal="Build a portfolio project",
        deadline_months=4,
        weekly_hours=8,
        current_level="Intermediate Python",
    )
    analysis = GoalAnalyzeResponse(
        clarified_goal="Build a portfolio project in 4 months",
        feasible=True,
        risk_level=RiskLevel.medium,
        main_risks=["Scope creep"],
        missing_inputs=[],
        recommendation="Ship one small project end to end",
        first_action="Define the project scope",
    )

    with patch("app.services.goal_service.analyze_goal", return_value=analysis) as mock_analyze_goal, patch(
        "app.services.goal_service.save_analysis", return_value=goal
    ) as mock_save_analysis:
        result = analyze_saved_goal(db, goal)

    assert result is analysis
    mock_analyze_goal.assert_called_once()
    request = mock_analyze_goal.call_args.args[0]
    assert request.goal == goal.goal
    assert request.deadline_months == goal.deadline_months
    assert request.weekly_hours == goal.weekly_hours
    assert request.current_level == goal.current_level
    mock_save_analysis.assert_called_once_with(db, goal, analysis.model_dump_json())
