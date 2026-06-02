from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_analyze_goal_validation_error():
    response = client.post("/goals/analyze", json={
        "goal": "AI",
        "deadline_months": 0,
        "weekly_hours": 0,
        "current_level": "x"
    })

    assert response.status_code == 422