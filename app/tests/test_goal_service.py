from datetime import datetime
from unittest.mock import MagicMock, patch

from app.db.models import GoalEntity
from app.schemas import AnalysisStatus, GoalAnalyzeResponse, GoalCreateRequest, GoalUpdateRequest, RiskLevel
from app.services.goal_service import analyze_saved_goal, build_goal_detail_response, create_new_goal, get_goal, update_goal


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
        "app.services.goal_service.goal_repository.create_goal", return_value=expected_entity
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

    with patch("app.services.goal_service.goal_repository.get_goal_by_id", return_value=expected_entity) as mock_get_goal:
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

    with patch("app.services.goal_service.goal_analyzer.analyze_goal", return_value=analysis) as mock_analyze_goal, patch(
        "app.services.goal_service.goal_repository.save_analysis", return_value=goal
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


def test_update_goal_delegates_to_repository():
    db = MagicMock()
    request = GoalUpdateRequest(
        goal="Update goal",
        weekly_hours=10,
    )
    expected_entity = GoalEntity(
        id="goal-123",
        deadline_months=6,
        weekly_hours=10,
        current_level="Intermediate Python",
    )

    with patch("app.services.goal_service.goal_repository.update_goal", return_value=expected_entity) as mock_update_goal:
        result = update_goal(db, "goal-123", request)

    assert result is expected_entity
    mock_update_goal.assert_called_once_with(db, "goal-123", {"goal": "Update goal", "weekly_hours": 10})


def test_build_goal_detail_response_without_analysis():
    goal = GoalEntity(
        id="goal-123",
        goal="Build a portfolio project",
        deadline_months=4,
        weekly_hours=8,
        current_level="Intermediate Python",
    )

    result = build_goal_detail_response(goal)

    assert result.id == goal.id
    assert result.analysis_status == AnalysisStatus.not_analyzed
    assert result.analysis is None


def test_build_goal_detail_response_with_analysis():
    analysis = GoalAnalyzeResponse(
        clarified_goal="Build a portfolio project in 4 months",
        feasible=True,
        risk_level=RiskLevel.medium,
        main_risks=["Scope creep"],
        missing_inputs=[],
        recommendation="Ship one small project end to end",
        first_action="Define the project scope",
    )
    goal = GoalEntity(
        id="goal-123",
        goal="Build a portfolio project",
        deadline_months=4,
        weekly_hours=8,
        current_level="Intermediate Python",
        analysis_json=analysis.model_dump_json(),
        analysis_status="analyzed",
        analysis_updated_at=datetime(2026, 6, 24, 12, 0, 0),
    )

    result = build_goal_detail_response(goal)

    assert result.analysis_status == AnalysisStatus.analyzed
    assert result.analysis_updated_at == datetime(2026, 6, 24, 12, 0, 0)
    assert result.analysis is not None
    assert result.analysis.clarified_goal == analysis.clarified_goal
    assert result.analysis.feasible == analysis.feasible
    assert result.analysis.risk_level == analysis.risk_level
