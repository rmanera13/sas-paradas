import os
import pytest
from app import create_app

# Por padrão testa em SQLite. Para testar no PostgreSQL:
#   TEST_DATABASE_URL=postgresql://usuario:senha@host/banco pytest -v
PG_URL = os.environ.get("TEST_DATABASE_URL")


@pytest.fixture
def app(tmp_path):
    if PG_URL:
        a = create_app({"TESTING": True, "DATABASE": PG_URL})
        with a.app_context():
            from app.db import get_db
            db = get_db()
            db.execute("TRUNCATE parada, usuario RESTART IDENTITY CASCADE")
            db.commit()
        return a
    return create_app({"TESTING": True, "DATABASE": str(tmp_path / "t.sqlite")})


@pytest.fixture
def client(app):
    return app.test_client()
