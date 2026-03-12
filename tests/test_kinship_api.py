import os
import sys

import pytest
from fastapi.testclient import TestClient

# make sure the repository root is on PYTHONPATH so we can import `app`
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from app.db import engine
from app.models.family import Base

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    engine.dispose()
    if os.path.exists("test.db"):
        os.remove("test.db")
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    if os.path.exists("test.db"):
        os.remove("test.db")


def _seed_via_api():
    # Grandparents
    client.post(
        "/api/v1/individuals/",
        json={"name": "Sekuru", "gender": "male", "birth_date": "1940-01-01"},
    )
    client.post(
        "/api/v1/individuals/",
        json={"name": "Ambuya", "gender": "female", "birth_date": "1945-01-01"},
    )

    # Parents/aunt
    client.post(
        "/api/v1/individuals/",
        json={"name": "Baba", "gender": "male", "birth_date": "1970-01-01"},
    )
    client.post(
        "/api/v1/individuals/",
        json={"name": "Tete", "gender": "female", "birth_date": "1972-01-01"},
    )
    client.post(
        "/api/v1/individuals/",
        json={"name": "Amai", "gender": "female", "birth_date": "1973-01-01"},
    )

    # Child
    client.post(
        "/api/v1/individuals/",
        json={"name": "Tawanda", "gender": "male", "birth_date": "2000-01-01"},
    )

    # Relationships
    client.post("/api/v1/relationships/", json={"parent_id": 1, "child_id": 3, "type": "biological"})
    client.post("/api/v1/relationships/", json={"parent_id": 2, "child_id": 3, "type": "biological"})
    client.post("/api/v1/relationships/", json={"parent_id": 1, "child_id": 4, "type": "biological"})
    client.post("/api/v1/relationships/", json={"parent_id": 2, "child_id": 4, "type": "biological"})
    client.post("/api/v1/relationships/", json={"parent_id": 3, "child_id": 6, "type": "biological"})
    client.post("/api/v1/relationships/", json={"parent_id": 5, "child_id": 6, "type": "biological"})


def test_get_kinship_success():
    _seed_via_api()

    # Tawanda (6) -> Baba (3)
    resp = client.get("/api/v1/kinship/", params={"person_id": 6, "relative_id": 3})
    assert resp.status_code == 200
    data = resp.json()
    assert data["person_id"] == 6
    assert data["relative_id"] == 3
    assert data["english_relationship"] == "father"
    assert data["shona_relationship"] == "baba"

    # Tawanda (6) -> Tete (4)
    resp = client.get("/api/v1/kinship/", params={"person_id": 6, "relative_id": 4})
    assert resp.status_code == 200
    data = resp.json()
    assert data["english_relationship"] == "aunt"
    assert data["shona_relationship"] == "tete"


def test_get_kinship_not_found():
    _seed_via_api()

    resp = client.get("/api/v1/kinship/", params={"person_id": 999, "relative_id": 3})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Person not found"

    resp = client.get("/api/v1/kinship/", params={"person_id": 6, "relative_id": 999})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Relative not found"
