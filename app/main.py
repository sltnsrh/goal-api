from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.database import init_db
from app.routers.goals import router as goals_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Goal OS API", version="0.1.0", lifespan=lifespan)
app.include_router(goals_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Check API health status.

    Returns:
        Dictionary with status key indicating service is operational.
    """
    return {"status": "ok"}
