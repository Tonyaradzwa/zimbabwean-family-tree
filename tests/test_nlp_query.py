"""
Tests for the POST /api/v1/query/ endpoint.

OpenAI is mocked throughout so no network call or API key is needed.
The mock patches app.nlp.chat._parse_intent, which is the only function
that talks to the model; everything else (DB lookup, kinship engine) runs
for real against the test SQLite database.
"""

import os
import sys
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

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


def _seed():
    """Seed a minimal family: Sekuru → Baba → Tawanda, with Amai as co-parent."""
    client.post("/api/v1/individuals/", json={"name": "Sekuru", "gender": "male", "birth_date": "1940-01-01"})
    client.post("/api/v1/individuals/", json={"name": "Baba",   "gender": "male", "birth_date": "1970-01-01"})
    client.post("/api/v1/individuals/", json={"name": "Amai",   "gender": "female", "birth_date": "1973-01-01"})
    client.post("/api/v1/individuals/", json={"name": "Tawanda","gender": "male", "birth_date": "2000-01-01"})

    client.post("/api/v1/relationships/", json={"parent_id": 1, "child_id": 2, "type": "biological"})
    client.post("/api/v1/relationships/", json={"parent_id": 2, "child_id": 4, "type": "biological"})
    client.post("/api/v1/relationships/", json={"parent_id": 3, "child_id": 4, "type": "biological"})


# ---------------------------------------------------------------------------
# Successful parse + match
# ---------------------------------------------------------------------------

def test_query_finds_father():
    """
    "Who is Tawanda's father?" → OpenAI returns the intent, engine finds Baba.
    """
    _seed()

    fake_intent = {"subject_name": "Tawanda", "relationship_asked": "father"}
    with patch("app.nlp.chat._parse_intent", return_value=fake_intent):
        resp = client.post("/api/v1/query/", json={"query": "Who is Tawanda's father?"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["subject_name"] == "Tawanda"
    assert data["relationship_asked"] == "father"
    assert "Baba" in data["answer"]
    assert data["subject_id"] is not None


def test_query_unknown_person():
    """
    When the extracted name doesn't exist in the DB, a clear message is returned.
    """
    _seed()

    fake_intent = {"subject_name": "NoSuchPerson", "relationship_asked": "mother"}
    with patch("app.nlp.chat._parse_intent", return_value=fake_intent):
        resp = client.post("/api/v1/query/", json={"query": "Who is NoSuchPerson's mother?"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["subject_id"] is None
    assert "nosuchperson" in data["answer"].lower()


def test_query_no_matching_relatives():
    """
    When the person exists but has no recorded relative of that type, say so.
    """
    _seed()

    # Sekuru has no aunt in the seeded tree
    fake_intent = {"subject_name": "Sekuru", "relationship_asked": "aunt"}
    with patch("app.nlp.chat._parse_intent", return_value=fake_intent):
        resp = client.post("/api/v1/query/", json={"query": "Who is Sekuru's aunt?"})

    assert resp.status_code == 200
    data = resp.json()
    assert "no" in data["answer"].lower()


def test_query_no_relationship_term_returns_all():
    """
    When relationship_asked is null, all known relatives are listed.
    """
    _seed()

    fake_intent = {"subject_name": "Tawanda", "relationship_asked": None}
    with patch("app.nlp.chat._parse_intent", return_value=fake_intent):
        resp = client.post("/api/v1/query/", json={"query": "Tell me about Tawanda's family."})

    assert resp.status_code == 200
    data = resp.json()
    assert "Baba" in data["answer"]
    assert "Amai" in data["answer"]


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------

def test_query_returns_503_when_openai_unavailable():
    """
    If _parse_intent raises RuntimeError (missing key / package), the endpoint
    surfaces a 503 rather than a 500.
    """
    _seed()

    with patch("app.nlp.chat._parse_intent", side_effect=RuntimeError("OPENAI_API_KEY environment variable is not set.")):
        resp = client.post("/api/v1/query/", json={"query": "Who is Tawanda's father?"})

    assert resp.status_code == 503
    assert "OPENAI_API_KEY" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Edge cases requested by product requirements
# ---------------------------------------------------------------------------

def test_query_misspelled_name_fuzzy_match():
    """
    Slight misspelling should still resolve via fuzzy DB matching.
    Example: Tafadswa -> Tafadzwa.
    """
    _seed()
    client.post("/api/v1/individuals/", json={"name": "Tafadzwa", "gender": "male", "birth_date": "2001-01-01"})

    fake_intent = {"subject_name": "Tafadswa", "relationship_asked": None}
    with patch("app.nlp.chat._parse_intent", return_value=fake_intent):
        resp = client.post("/api/v1/query/", json={"query": "Tell me about Tafadswa's family."})

    assert resp.status_code == 200
    data = resp.json()
    # The resolver should return the matched canonical DB name.
    assert data["subject_name"] == "Tafadzwa"
    assert data["subject_id"] is not None


def test_query_honorific_handled_by_prompt_extraction():
    """
    Honorific behavior is prompt-driven now. This test emulates OpenAI
    extracting the clean name from "Mr. Tafadzwa".
    """
    _seed()
    client.post("/api/v1/individuals/", json={"name": "Tafadzwa", "gender": "male", "birth_date": "2001-01-01"})

    # Prompt should normalize "Mr. Tafadzwa" -> "Tafadzwa".
    fake_intent = {"subject_name": "Tafadzwa", "relationship_asked": None}
    with patch("app.nlp.chat._parse_intent", return_value=fake_intent):
        resp = client.post("/api/v1/query/", json={"query": "Tell me about Mr. Tafadzwa's family."})

    assert resp.status_code == 200
    data = resp.json()
    assert data["subject_name"] == "Tafadzwa"
    assert data["subject_id"] is not None


def test_query_mixed_case_name():
    """
    Mixed case should match via case-insensitive lookup.
    """
    _seed()

    fake_intent = {"subject_name": "taWaNda", "relationship_asked": "father"}
    with patch("app.nlp.chat._parse_intent", return_value=fake_intent):
        resp = client.post("/api/v1/query/", json={"query": "Who is taWaNda's father?"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["subject_name"] == "Tawanda"
    assert "Baba" in data["answer"]


def test_query_two_name_disambiguation_pattern():
    """
    Pattern: "who is tafadzwa to Elli's sister?"
    We expect prompt extraction to choose Elli as subject and Tafadzwa as
    relative_name. The endpoint should then answer the relationship from
    Elli's perspective.
    """
    _seed()

    # Add Elli and Elli's sister branch plus Tafadzwa.
    client.post("/api/v1/individuals/", json={"name": "Elli", "gender": "female", "birth_date": "2000-01-01"})
    client.post("/api/v1/individuals/", json={"name": "ElliSister", "gender": "female", "birth_date": "2002-01-01"})
    client.post("/api/v1/individuals/", json={"name": "ElliParent1", "gender": "male", "birth_date": "1970-01-01"})
    client.post("/api/v1/individuals/", json={"name": "ElliParent2", "gender": "female", "birth_date": "1972-01-01"})
    client.post("/api/v1/individuals/", json={"name": "Tafadzwa", "gender": "male", "birth_date": "2001-01-01"})

    # IDs after _seed() are predictable in this test DB sequence:
    # 1 Sekuru, 2 Baba, 3 Amai, 4 Tawanda, then:
    # 5 Elli, 6 ElliSister, 7 ElliParent1, 8 ElliParent2, 9 Tafadzwa
    client.post("/api/v1/relationships/", json={"parent_id": 7, "child_id": 5, "type": "biological"})
    client.post("/api/v1/relationships/", json={"parent_id": 8, "child_id": 5, "type": "biological"})
    client.post("/api/v1/relationships/", json={"parent_id": 7, "child_id": 6, "type": "biological"})
    client.post("/api/v1/relationships/", json={"parent_id": 8, "child_id": 6, "type": "biological"})

    fake_intent = {
        "subject_name": "Elli",
        "relative_name": "Tafadzwa",
        "relationship_asked": "sister",
    }
    with patch("app.nlp.chat._parse_intent", return_value=fake_intent):
        resp = client.post("/api/v1/query/", json={"query": "Who is tafadzwa to Elli's sister?"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["subject_name"] == "Elli"
    assert data["subject_id"] is not None
    # No sibling relationship exists between Elli and Tafadzwa in this seed.
    # The endpoint should still produce a deterministic relationship answer.
    assert "Tafadzwa" in data["answer"]
