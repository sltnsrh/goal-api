import os
from datetime import date, timedelta

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from app.schemas import GoalPlanRequest, GoalPlanResponse, Milestone

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=20.0,
)
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5-mini")

PLAN_SYSTEM_PROMPT = (
    "You are an execution-planning assistant. "
    "Turn the user's goal into a realistic, concrete plan that fits the available time. "
    "Be explicit, conservative, and specific. "
    "Use only the information provided. Do not ask follow-up questions, invent facts, "
    "or add motivational language. Return only the structured plan."
)


class _MilestoneRaw(BaseModel):
    title: str
    start_date: date
    end_date: date


class _GoalPlanRaw(BaseModel):
    current_phase: str
    milestones: list[_MilestoneRaw]
    next_week_tasks: list[str]


def _build_analysis_context(request: GoalPlanRequest) -> str:
    if not request.analysis:
        return "Prior analysis: none"

    risks = "; ".join(request.analysis.main_risks) if request.analysis.main_risks else "none"
    return (
        "Prior analysis:\n"
        f"- risk_level: {request.analysis.risk_level.value}\n"
        f"- main_risks: {risks}\n"
        f"- recommendation: {request.analysis.recommendation}"
    )


def _build_user_prompt(request: GoalPlanRequest) -> str:
    today = date.today()
    deadline = today + timedelta(weeks=request.deadline_months * 4)
    return (
        "Create a concrete execution plan.\n\n"
        f"Goal: {request.goal}\n"
        f"Start date: {today.isoformat()}\n"
        f"Deadline: {deadline.isoformat()} ({request.deadline_months} months)\n"
        f"Weekly hours: {request.weekly_hours} hours/week\n"
        f"Current level: {request.current_level}\n\n"
        f"{_build_analysis_context(request)}\n\n"
        "Planning rules:\n"
        "1. Treat any prior analysis as the strongest constraint.\n"
        "2. Be conservative. Prefer fewer, higher-leverage milestones over optimistic overplanning.\n"
        "3. Use 1 to 6 milestones. Short deadlines should use fewer milestones; long deadlines should be compressed into major phases, never more than 6 total.\n"
        "4. Each milestone title must describe a concrete deliverable or outcome that can be verified "
        "(e.g. 'Publish first article', 'Complete certification exam'), "
        "not a learning activity (not 'Study topic X', 'Improve skill Y'). "
        "Order milestones chronologically.\n"
        "5. Set start_date and end_date as ISO dates (YYYY-MM-DD). "
        "The first milestone starts on the start date. "
        "The last milestone ends on the deadline date. "
        "Milestones must not overlap and must cover the full timeline.\n"
        "6. Keep next_week_tasks to 3 to 5 actions, ordered by priority. Each task must be specific enough "
        "to verify completion — include the resource, chapter, or expected output "
        "(e.g. 'Complete week 1 of Couch to 5K training plan', 'Submit first cover letter to three target companies'). "
        "Name real resources appropriate to the goal. "
        "When prior analysis is provided, at least one task must directly address the highest-priority risk.\n"
        "7. Use short, direct phrases. No extra commentary, no questions, and no reasoning trace.\n"
        "8. Set current_phase to a short phase name that describes where the learner is now "
        "One to three words, no numbering.\n"
    )


def _compute_total_hours(m: _MilestoneRaw, weekly_hours: int) -> int:
    """Compute focused work hours from date range and weekly availability."""
    weeks = round((m.end_date - m.start_date).days / 7)
    return weeks * weekly_hours


def generate_plan(request: GoalPlanRequest) -> GoalPlanResponse:
    """Generate a structured execution plan for a goal using OpenAI.

    Args:
        request: The goal plan request with goal details and optional prior analysis.

    Returns:
        Structured plan response with milestones and computed total hours.

    Raises:
        ValueError: If OpenAI response parsing fails.
    """
    response = client.responses.parse(
        model=MODEL,
        input=[
            {
                "role": "system",
                "content": PLAN_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": _build_user_prompt(request),
            },
        ],
        text_format=_GoalPlanRaw,
    )

    if response.output_parsed is None:
        raise ValueError("Failed to parse generated plan response")

    raw = response.output_parsed
    milestones = [
        Milestone(
            title=m.title,
            start_date=m.start_date,
            end_date=m.end_date,
            total_hours=_compute_total_hours(m, request.weekly_hours),
        )
        for m in raw.milestones
    ]
    return GoalPlanResponse(
        current_phase=raw.current_phase,
        milestones=milestones,
        next_week_tasks=raw.next_week_tasks,
    )
