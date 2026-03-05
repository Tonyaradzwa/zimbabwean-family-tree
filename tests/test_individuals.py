import os
import pytest
import sys
from fastapi.testclient import TestClient

# make sure the repository root is on PYTHONPATH so we can import `app`
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from app.db import engine
from app.models.family import Base

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    # ensure a clean database for each test run
    if os.path.exists("test.db"):
        os.remove("test.db")
    Base.metadata.create_all(bind=engine)
    yield
    if os.path.exists("test.db"):
        os.remove("test.db")


def test_individuals_crud():
    # create an individual
    resp = client.post(
        "/api/v1/individuals/",
        json={"name": "Alice", "gender": "female", "birth_date": "1990-01-01"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 1
    assert data["name"] == "Alice"

    # list individuals
    resp = client.get("/api/v1/individuals/")
    assert resp.status_code == 200
    all_people = resp.json()
    assert isinstance(all_people, list)
    assert len(all_people) == 1

    # get specific individual
    resp = client.get("/api/v1/individuals/1")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Alice"

    # update the individual
    resp = client.put(
        "/api/v1/individuals/1",
        json={"name": "Alice Updated", "gender": "female", "birth_date": "1990-01-01"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Alice Updated"

    # delete the individual
    resp = client.delete("/api/v1/individuals/1")
    assert resp.status_code == 200
    assert "deleted successfully" in resp.json()["message"]

    # verify deletion returns 404
    resp = client.get("/api/v1/individuals/1")
    assert resp.status_code == 404
