"""Pruebas aisladas: SQLite temporal creada exclusivamente con Alembic."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import delete

test_dir = TemporaryDirectory(prefix="examen-auth-")
test_url = f"sqlite:///{Path(test_dir.name) / 'test.db'}"
os.environ["DATABASE_URL"] = test_url
os.environ["DATABASE_URL_DIRECT"] = test_url
os.environ["SECRET_KEY"] = "clave-aislada-para-pruebas-de-usuarios-123456789"
os.environ["CORS_ORIGINS"] = '["http://localhost:5173"]'

from app.database import SessionLocal, engine
from app.main import app
from app.models import Usuario


@pytest.fixture(scope="session", autouse=True)
def migrated_database():
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(config, "head")
    yield
    command.downgrade(config, "base")
    engine.dispose()
    test_dir.cleanup()


@pytest.fixture
def client(migrated_database):
    with SessionLocal() as db:
        db.execute(delete(Usuario))
        db.commit()
    with TestClient(app) as client:
        yield client
