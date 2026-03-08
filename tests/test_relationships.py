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


def test_relationships_crud():
    # create parent and child individuals first
    resp = client.post(
        "/api/v1/individuals/",
        json={"name": "Parent One", "gender": "female", "birth_date": "1970-01-01"},
    )
    assert resp.status_code == 200

    resp = client.post(
        "/api/v1/individuals/",
        json={"name": "Child One", "gender": "male", "birth_date": "2000-01-01"},
    )
    assert resp.status_code == 200

    # create relationship
    resp = client.post(
        "/api/v1/relationships/",
        json={"parent_id": 1, "child_id": 2, "type": "biological"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 1
    assert data["parent_id"] == 1
    assert data["child_id"] == 2
    assert data["type"] == "biological"

    # list relationships
    resp = client.get("/api/v1/relationships/")
    assert resp.status_code == 200
    all_relationships = resp.json()
    assert isinstance(all_relationships, list)
    assert len(all_relationships) == 1

    # get specific relationship
    resp = client.get("/api/v1/relationships/1")
    assert resp.status_code == 200
    relationship = resp.json()
    assert relationship["parent_id"] == 1
    assert relationship["child_id"] == 2

    # delete relationship
    resp = client.delete("/api/v1/relationships/1")
    assert resp.status_code == 200
    assert "deleted successfully" in resp.json()["message"]

    # verify deletion returns 404
    resp = client.get("/api/v1/relationships/1")
    assert resp.status_code == 404


def test_relationship_validations():
    # create two individuals
    resp = client.post(
        "/api/v1/individuals/",
        json={"name": "Valid Parent", "gender": "male", "birth_date": "1980-01-01"},
    )
    assert resp.status_code == 200

    resp = client.post(
        "/api/v1/individuals/",
        json={"name": "Valid Child", "gender": "female", "birth_date": "2010-01-01"},
    )
    assert resp.status_code == 200

    # reject self-parenting relationship
    resp = client.post(
        "/api/v1/relationships/",
        json={"parent_id": 1, "child_id": 1, "type": "biological"},
    )
    assert resp.status_code == 400

    # reject duplicate relationship
    resp = client.post(
        "/api/v1/relationships/",
        json={"parent_id": 1, "child_id": 2, "type": "biological"},
    )
    assert resp.status_code == 200

    resp = client.post(
        "/api/v1/relationships/",
        json={"parent_id": 1, "child_id": 2, "type": "biological"},
    )
    assert resp.status_code == 400

    # missing parent should return 404
    resp = client.post(
        "/api/v1/relationships/",
        json={"parent_id": 999, "child_id": 2, "type": "biological"},
    )
    assert resp.status_code == 404

    # missing child should return 404
    resp = client.post(
        "/api/v1/relationships/",
        json={"parent_id": 1, "child_id": 999, "type": "biological"},
    )
    assert resp.status_code == 404
