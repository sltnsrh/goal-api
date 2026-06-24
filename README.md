# Goal OS API

Goal OS API is a FastAPI backend for goal tracking and AI-assisted planning, built around structured outputs, clean service boundaries, and persistence.

## Why this project exists

Goal OS API is a learning project focused on production-style AI integration patterns:

- FastAPI
- Structured Outputs
- OpenAI SDK
- Resource-based REST APIs
- Persistence
- AI workflow orchestration

## What it does

- Create goals
- List goals with pagination
- View goal details with analysis state
- Analyze a saved goal with OpenAI
- Update a goal with `PATCH`
- Generate a plan only after a feasible analysis

## API flow

1. `POST /goals`
2. `POST /goals/{goal_id}/analyze`
3. `PATCH /goals/{goal_id}` if the goal changes
4. `POST /goals/{goal_id}/analyze` again
5. `POST /goals/{goal_id}/plan`

## Example

Create a goal:

```json
{
  "goal": "Become AI Integration Engineer",
  "deadline_months": 12,
  "weekly_hours": 8,
  "current_level": "Java Backend Developer"
}
```

### Endpoints

- `GET /health`
- `POST /goals`
- `GET /goals`
- `GET /goals/{goal_id}`
- `PATCH /goals/{goal_id}`
- `POST /goals/{goal_id}/analyze`
- `POST /goals/{goal_id}/plan`

## Tech stack

- FastAPI
- Pydantic v2
- SQLAlchemy
- SQLite
- OpenAI API

## Environment

Required:

- `OPENAI_API_KEY`

Optional:

- `OPENAI_MODEL` - defaults to `gpt-5.5-mini`
- `SQLITE_DATABASE_PATH` - defaults to `./data/goals.db`

## Run locally

```bash
uvicorn app.main:app --reload
```

The database file is created automatically if it does not exist.

## Tests

```bash
pytest -q
```

## Project structure

- `app/routers` - HTTP endpoints
- `app/services` - business logic and OpenAI integration
- `app/repositories` - database access
- `app/db` - SQLAlchemy setup and models
- `app/schemas.py` - request/response contracts

## Architecture

```text
Client
  ↓
FastAPI
  ↓
Services
  ↓
Repositories
  ↓
SQLite
OpenAI
  ↑
Goal Analysis / Goal Planning
```

## Current Status

Implemented:

- Goal persistence
- Goal analysis
- Goal updates
- Goal planning
- Test coverage

Planned:

- PostgreSQL
- Docker
- CI/CD
- Cloud Run deployment

## Notes

- `GET /goals` returns a compact list response.
- `GET /goals/{goal_id}` returns goal details plus analysis state and parsed analysis payload.
- `POST /goals/{goal_id}/plan` returns `409 Conflict` unless the goal has been analyzed and `feasible == true`.
- SQLite data lives outside git in `./data/goals.db`.
