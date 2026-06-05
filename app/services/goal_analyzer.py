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
    prompt = f"""
You are a practical goal mentor.

Analyze this goal and return a strict structured response.

Goal: {request.goal}
Deadline months: {request.deadline_months}
Weekly hours: {request.weekly_hours}
Current level: {request.current_level}

Be realistic, specific, and concise.
"""
    
    response = client.responses.parse(
        model=MODEL,
        input=[
            {
                "role": "system",
                "content": "You analyze personal/professional goals and return structured output only.",
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
        text_format=GoalAnalyzeResponse,
    )

    if response.output_parsed is None:
        raise ValueError("Failed to parse goal analysis response")
    return response.output_parsed