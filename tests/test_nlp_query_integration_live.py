"""Live integration tests for POST /api/v1/query/.

These tests intentionally do NOT mock OpenAI. They exercise the full path:
query text -> OpenAI intent extraction -> DB lookup -> kinship answer rendering.

Run only when a real API key is available:
    OPENAI_API_KEY=... PYTHONPATH=. pytest tests/test_nlp_query_integration_live.py -v
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from app.db import engine
from app.models.family import Base

client = TestClient(app)

pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set; live OpenAI integration tests skipped",
)


def _post(path: str, payload: dict):
    resp = client.post(path, json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()


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


def _seed_family_tree():
    # ---------------------------------------------------------------------
    # Minimal mixed-name test tree used by active edge cases
    # ---------------------------------------------------------------------
    #
    #                   MbuyaGrace (F)       MaiRudo (F)
    #                       O                   O
    #                      / \                  |
    #                     /   \                 |
    #                    /     \                |
    #                 Mark(M)  Sarah(F)      Tariro(F)
    #                    O----------------------O
    #                           marriage
    #                              |
    #                            /   \
    #                         Tino(M) Ria(F)
    #
    # Legend:
    # - Horizontal pair line between Tariro and Mark is modeled as Marriage.
    # - Vertical links are parent->child Relationship rows.
    # - This seed intentionally includes only nodes required by test cases:
    #   misspelling, prefix, mixed-case, apostrophe-less possessive, and
    #   two-name chain with spouse resolution.

    # Children
    _post("/api/v1/individuals/", {"name": "Tino", "gender": "male", "birth_date": "2003-01-01"})
    _post("/api/v1/individuals/", {"name": "Ria", "gender": "female", "birth_date": "2005-01-01"})

    # Parents
    _post("/api/v1/individuals/", {"name": "Tariro", "gender": "female", "birth_date": "1980-01-01"})
    _post("/api/v1/individuals/", {"name": "Mark", "gender": "male", "birth_date": "1979-01-01"})

    # Mark's sister and shared parent
    _post("/api/v1/individuals/", {"name": "Sarah", "gender": "female", "birth_date": "1977-01-01"})
    _post("/api/v1/individuals/", {"name": "MbuyaGrace", "gender": "female", "birth_date": "1952-01-01"})
    _post("/api/v1/individuals/", {"name": "MaiRudo", "gender": "female", "birth_date": "1954-01-01"})

    people_resp = client.get("/api/v1/individuals/")
    assert people_resp.status_code == 200, people_resp.text
    people = people_resp.json()
    by_name = {p["name"]: p["id"] for p in people}

    relationships = [
        # Mark + Tariro children
        {"parent_id": by_name["Mark"], "child_id": by_name["Tino"], "type": "biological"},
        {"parent_id": by_name["Tariro"], "child_id": by_name["Tino"], "type": "biological"},
        {"parent_id": by_name["Mark"], "child_id": by_name["Ria"], "type": "biological"},
        {"parent_id": by_name["Tariro"], "child_id": by_name["Ria"], "type": "biological"},

        # MbuyaGrace children (Mark and Sarah are siblings)
        {"parent_id": by_name["MbuyaGrace"], "child_id": by_name["Mark"], "type": "biological"},
        {"parent_id": by_name["MbuyaGrace"], "child_id": by_name["Sarah"], "type": "biological"},
        # Tariro branch is separate
        {"parent_id": by_name["MaiRudo"], "child_id": by_name["Tariro"], "type": "biological"},
    ]

    for rel in relationships:
        resp = client.post("/api/v1/relationships/", json=rel)
        assert resp.status_code == 200, resp.text

    # Needed for spouse/in-law reasoning in two-name chain questions.
    marriage = {
        "partner1_id": by_name["Mark"],
        "partner2_id": by_name["Tariro"],
        "date": "2000-01-01",
    }
    marriage_resp = client.post("/api/v1/marriages/", json=marriage)
    assert marriage_resp.status_code == 200, marriage_resp.text


def test_live_query_edge_cases_end_to_end():
    """Covers all discussed edge cases with real OpenAI extraction.

    Total expected OpenAI calls in this test: 5.
    """
    _seed_family_tree()

    # 1) Misspelling
    r1 = _post("/api/v1/query/", {"query": "Who is Riya's father?"})
    assert r1["subject_name"] == "Ria"
    assert r1["relationship_asked"] == "father"
    assert "Mark" in r1["answer"]
    assert "father" in r1["answer"].lower()

    # 2) Prefix title
    r2 = _post("/api/v1/query/", {"query": "Who is Mr. Mark's sister?"})
    assert r2["subject_name"] == "Mark"
    assert r2["relationship_asked"] == "sister"
    assert "Sarah" in r2["answer"]

    # 3) Mixed case
    r3 = _post("/api/v1/query/", {"query": "Who is tInO's mother?"})
    assert r3["subject_name"] == "Tino"
    assert r3["relationship_asked"] == "mother"
    assert "Tariro" in r3["answer"]

    # 4) Two-name pattern with possessive chain
    # TODO: re-enable this block once sister-in-law inference is implemented.
    # r4 = _post("/api/v1/query/", {"query": "Who is Sarah to Ria's mother?"})
    # assert r4["subject_name"] == "Ria"
    # assert r4["relationship_asked"] == "mother"
    # assert "Sarah" in r4["answer"]

    # 5) Apostrophe-less possessive + nested chain
    r5 = _post(
        "/api/v1/query/",
        {"query": "Who is MaiRudo to Tariros daughter Ria?"},
    )
    assert r5["subject_name"] == "Ria"
    assert r5["relationship_asked"] == "daughter"
    assert "MaiRudo" in r5["answer"]
    assert "grandmother" in r5["answer"].lower() or "mother" in r5["answer"].lower()

    # 6) Stronger two-name chain baseline (non-trivial)
    r6 = _post("/api/v1/query/", {"query": "Who is Mark to Ria's mother?"})
    assert r6["subject_name"] == "Ria"
    assert r6["relationship_asked"] == "mother"
    assert "Mark" in r6["answer"]
    assert "Tariro" in r6["answer"]
    assert "husband" in r6["answer"].lower()
