import os
from openai import OpenAI
from dotenv import load_dotenv

from app.schemas import GoalAnalyzeRequest, GoalAnalyzeResponse

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=20.0,
)
MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-nano")

def analyze_goal(request: GoalAnalyzeRequest) -> GoalAnalyzeResponse:
    """Analyze a goal using OpenAI and return structured analysis.

    Args:
        request: The goal analysis request with goal details.

    Returns:
        Structured goal analysis response from OpenAI.

    Raises:
        ValueError: If OpenAI response parsing fails.
    """
    response = client.responses.parse(
        model=MODEL,
        input=[
            {
                "role": "system",
                "content": (
                    "You are a strict, experienced goal coach. "
                    "You evaluate goals honestly — no motivation fluff. "
                    "Identify real risks, give specific actionable milestones, "
                    "and assess feasibility based on time and skill level. "
                    "Return structured output only."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Goal: {request.goal}\n"
                    f"Deadline: {request.deadline_months} months\n"
                    f"Weekly availability: {request.weekly_hours} hours\n"
                    f"Current level: {request.current_level}\n\n"
                    "Analyze feasibility, identify the top risks, "
                    "and provide concrete monthly milestones."
                ),
            },
        ],
        text_format=GoalAnalyzeResponse,
    )

    if response.output_parsed is None:
        raise ValueError("Failed to parse goal analysis response")
    return response.output_parsed