import pytest
from datetime import date
from unittest.mock import MagicMock, patch

from app.schemas import GoalAnalyzeResponse, GoalPlanRequest, RiskLevel
from app.services.goal_planner import _GoalPlanRaw, _MilestoneRaw, _build_user_prompt, generate_plan

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
    assert "No extra commentary, no questions, and no reasoning trace." in prompt


@patch("app.services.goal_planner.client.responses.parse")
def test_plan_output_parsed_none_raises_value_error(mock_parse):
    mock_response = MagicMock()
    mock_response.output_parsed = None
    mock_parse.return_value = mock_response
    with pytest.raises(ValueError, match="Failed to parse generated plan response"):
        generate_plan(GoalPlanRequest(**_VALID_REQUEST))
