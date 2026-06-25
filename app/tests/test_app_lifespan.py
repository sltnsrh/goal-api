from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect

from app.db import database
from app.main import app


def test_lifespan_initializes_database(tmp_path, monkeypatch):
    db_path = tmp_path / "lifespan.db"
    test_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    monkeypatch.setattr(database, "engine", test_engine)

    with TestClient(app):
        pass

    assert inspect(test_engine).has_table("goals")
