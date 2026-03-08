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
    engine.dispose()
    if os.path.exists("test.db"):
        os.remove("test.db")
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    if os.path.exists("test.db"):
        os.remove("test.db")


def test_marriages_crud():
    # create spouse individuals first
    resp = client.post(
        "/api/v1/individuals/",
        json={"name": "Spouse One", "gender": "female", "birth_date": "1991-01-01"},
    )
    assert resp.status_code == 200

    resp = client.post(
        "/api/v1/individuals/",
        json={"name": "Spouse Two", "gender": "male", "birth_date": "1990-01-01"},
    )
    assert resp.status_code == 200

    # create marriage
    resp = client.post(
        "/api/v1/marriages/",
        json={"partner1_id": 1, "partner2_id": 2, "date": "2020-06-15"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 1
    assert data["partner1_id"] == 1
    assert data["partner2_id"] == 2
    assert data["date"] == "2020-06-15"

    # list marriages
    resp = client.get("/api/v1/marriages/")
    assert resp.status_code == 200
    all_marriages = resp.json()
    assert isinstance(all_marriages, list)
    assert len(all_marriages) == 1

    # get specific marriage
    resp = client.get("/api/v1/marriages/1")
    assert resp.status_code == 200
    marriage = resp.json()
    assert marriage["partner1_id"] == 1
    assert marriage["partner2_id"] == 2

    # delete marriage
    resp = client.delete("/api/v1/marriages/1")
    assert resp.status_code == 200
    assert "deleted successfully" in resp.json()["message"]

    # verify deletion returns 404
    resp = client.get("/api/v1/marriages/1")
    assert resp.status_code == 404


def test_marriage_validations():
    # create two individuals
    resp = client.post(
        "/api/v1/individuals/",
        json={"name": "Valid Spouse One", "gender": "male", "birth_date": "1987-01-01"},
    )
    assert resp.status_code == 200

    resp = client.post(
        "/api/v1/individuals/",
        json={"name": "Valid Spouse Two", "gender": "female", "birth_date": "1988-01-01"},
    )
    assert resp.status_code == 200

    # reject self-marriage
    resp = client.post(
        "/api/v1/marriages/",
        json={"partner1_id": 1, "partner2_id": 1, "date": "2021-01-01"},
    )
    assert resp.status_code == 400

    # reject duplicate marriage in same direction
    resp = client.post(
        "/api/v1/marriages/",
        json={"partner1_id": 1, "partner2_id": 2, "date": "2021-01-01"},
    )
    assert resp.status_code == 200

    resp = client.post(
        "/api/v1/marriages/",
        json={"partner1_id": 1, "partner2_id": 2, "date": "2021-01-01"},
    )
    assert resp.status_code == 400

    # reject duplicate marriage in reverse direction
    resp = client.post(
        "/api/v1/marriages/",
        json={"partner1_id": 2, "partner2_id": 1, "date": "2021-01-01"},
    )
    assert resp.status_code == 400

    # missing partner should return 404
    resp = client.post(
        "/api/v1/marriages/",
        json={"partner1_id": 999, "partner2_id": 2, "date": "2021-01-01"},
    )
    assert resp.status_code == 404

    # missing partner should return 404
    resp = client.post(
        "/api/v1/marriages/",
        json={"partner1_id": 1, "partner2_id": 999, "date": "2021-01-01"},
    )
    assert resp.status_code == 404
