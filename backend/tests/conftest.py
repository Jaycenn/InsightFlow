import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "test-only-secret-that-is-not-for-production"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)

    def session():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


def register(client, email="owner@example.com"):
    result = client.post("/api/auth/register", json={"name": "Owner", "email": email, "password": "safe-password-123"})
    assert result.status_code == 201, result.text
    return {"Authorization": f"Bearer {result.json()['access_token']}"}


def business(client, headers):
    result = client.post("/api/businesses", json={"name": "Courtside Supply Co."}, headers=headers)
    assert result.status_code == 201
    return result.json()["id"]
