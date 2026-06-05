from fastapi import FastAPI, HTTPException

from app.schemas import GoalAnalyzeRequest, GoalAnalyzeResponse
from app.services.goal_analyzer import analyze_goal

app = FastAPI(title="Goal OS API", version="0.1.0")

@app.get("/health")
def health() -> dict[str, str]:
    """Check API health status.

    Returns:
        Dictionary with status key indicating service is operational.
    """
    return {"status": "ok"}

@app.post("/goals/analyze", response_model=GoalAnalyzeResponse)
def analyze_goal_endpoint(request: GoalAnalyzeRequest) -> GoalAnalyzeResponse:
    """Analyze a goal and return structured analysis from AI.

    Args:
        request: The goal analysis request with goal details.

    Returns:
        Structured goal analysis response.

    Raises:
        HTTPException: If goal analysis fails with 502 status.
    """
    try:
        return analyze_goal(request)
    except (ValueError, OSError) as e:
        raise HTTPException(
            status_code=502,
            detail={
                "code": "AI_PROVIDER_ERROR",
                "message": str(e)
            }
        )