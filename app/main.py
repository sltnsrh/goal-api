from fastapi import FastAPI, HTTPException

from app.schemas import GoalAnalyzeRequest, GoalAnalyzeResponse, GoalPlanRequest, GoalPlanResponse
from app.services.goal_analyzer import analyze_goal
from app.services.goal_planner import generate_plan

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
    
@app.post("/goals/plan", response_model=GoalPlanResponse)
def generate_plan_endpoint(request: GoalPlanRequest) -> GoalPlanResponse:
    """Generate an execution plan for a goal using AI.

    Args:
        request: The goal plan request with goal details and optional prior analysis.

    Returns:
        Structured plan response with milestones and next week tasks.

    Raises:
        HTTPException: If plan generation fails with 502 status.
    """
    if request.analysis and not request.analysis.feasible:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "GOAL_NOT_FEASIBLE",
                "message": request.analysis.recommendation,
            },
        )
    try:
        return generate_plan(request)
    except (ValueError, OSError) as e:
        raise HTTPException(
            status_code=502,
            detail={
                "code": "AI_PROVIDER_ERROR",
                "message": str(e)
            }
        )