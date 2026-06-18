# Goal OS API

AI backend for goal analysis and planning.

## Current features

- POST /goals/analyze
- FastAPI
- Pydantic validation
- OpenAI structured output
- Basic tests

## Run locally

Set `SQLITE_DATABASE_PATH` if you want a different SQLite file location. The default is `./data/goals.db`.

```bash
uvicorn app.main:app --reload
