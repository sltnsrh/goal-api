from fastapi import FastAPI

from app.schemas import GoalAnalyzeRequest, GoalAnalyzeResponse
from app.services.goal_analyzer import analyze_goal

app = FastAPI(title="Goal OS API", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/goals/analyze", response_model=GoalAnalyzeResponse)
def analyze_goal_endpoint(request: GoalAnalyzeRequest):
    return analyze_goal(request)