"""
Natural-language kinship query handler.

Current implementation: OpenAI GPT is used to extract (subject_name,
relationship_term) from a free-text English question.  The extracted
intent is then resolved against the database using the existing kinship
engine to produce English and Shona answers.

TODO – alternatives to consider if OpenAI is not desired:
  1. Rule-based parser: regex patterns over a fixed vocabulary of
     relationship terms (fast, free, easy to unit-test, but brittle for
     unusual phrasing).
  2. Hybrid: attempt rule-based first; fall back to OpenAI only when the
     pattern does not match (best reliability/cost trade-off).
  3. Local model: run a small transformer (e.g. spaCy + en_core_web_sm,
     or a fine-tuned distilBERT) entirely offline (no API cost, no
     network dependency, slightly higher setup effort).
"""

import difflib
import json
import os
from typing import Optional

from sqlalchemy.orm import Session

# ---------------------------------------------------------------------------
# OpenAI client – imported lazily so the rest of the app still loads even
# if the `openai` package is not installed.
# ---------------------------------------------------------------------------
try:
    from openai import OpenAI as _OpenAI

    _openai_client: Optional[_OpenAI] = _OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY", "")
    )
except ImportError:  # pragma: no cover
    _openai_client = None

# Fuzzy-match cutoff: 0.0 = anything goes, 1.0 = exact only.
# 0.8 catches single-character swaps while avoiding false positives on short names.
_FUZZY_CUTOFF = 0.8

# ---------------------------------------------------------------------------
# System prompt – keep it narrow so the model always returns parseable JSON.
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = """
You are a kinship-query intent extractor for a family-tree application.

Given a natural-language English question about a family relationship,
return ONLY a valid JSON object with exactly these keys:

  "subject_name"       – the name of the person whose relatives are being
                         looked up.  Strip any honorific titles (Mr., Mrs.,
                         Dr., etc.) from the name.
  "relative_name"      – if the question mentions a SECOND person by name
                         (e.g. "who is Tafadzwa to Elli?"), put that second
                         name here; otherwise null.
  "relationship_asked" – the English kinship term being asked about
                         (e.g. "uncle", "mother", "cousin").  Use null
                         if the question asks for ANY/ALL relationships.

Critical extraction rules
-------------------------
1) If the query includes a relation chain like "Y's mother", "Y's daughter Z",
    "brother of Y", or "Fadzis daughter Tonya", resolve the final anchor person
    as follows:
    - If an explicit person name appears at the end of the chain (e.g. "daughter Tonya"),
      use that explicit name as subject_name.
    - Otherwise use the base named person in the chain (e.g. in "Tonya's mother",
      the base person is Tonya).
2) In "Who is X to <chain>?" questions, set relative_name = X and subject_name
    to the resolved anchor person from rule 1.
3) Treat apostrophe-less possessives as possessives when obvious:
    - "Fadzis" means "Fadzi's"
    - "Tonyas" means "Tonya's"
4) Keep names clean:
    - strip honorifics (Mr., Mrs., Dr., etc.)
    - keep hyphens inside names when present (e.g. Nyarie-Mary)

Do not include any explanation or markdown.  Return raw JSON only.

Examples
--------
Input : "Who is Tawanda's father?"
Output: {"subject_name": "Tawanda", "relative_name": null, "relationship_asked": "father"}

Input : "What is Rudo to Tendai?"
Output: {"subject_name": "Rudo", "relative_name": "Tendai", "relationship_asked": null}

Input : "Who is Tafadzwa to Elli's sister?"
Output: {"subject_name": "Elli", "relative_name": "Tafadzwa", "relationship_asked": "sister"}

Input : "Who is Louisa to Tonya's mother?"
Output: {"subject_name": "Tonya", "relative_name": "Louisa", "relationship_asked": "mother"}

Input : "Who is Unknown-Maternal-Parent to Fadzis daughter Tonya?"
Output: {"subject_name": "Tonya", "relative_name": "Unknown-Maternal-Parent", "relationship_asked": "daughter"}

Input : "Tell me about Mr. Chido's family."
Output: {"subject_name": "Chido", "relative_name": null, "relationship_asked": null}
""".strip()


def _parse_intent(query: str) -> dict:
    """Call OpenAI to extract intent from *query*.

    Returns a dict with keys ``subject_name`` and ``relationship_asked``.
    Raises ``RuntimeError`` if the OpenAI package is missing or the API key
    is not configured.

    TODO: replace or supplement this with a rule-based parser for common
    query shapes before reaching out to the model (see module docstring).
    """
    if _openai_client is None:
        raise RuntimeError(
            "openai package is not installed.  "
            "Run: pip install openai"
        )
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY environment variable is not set."
        )

    response = _openai_client.chat.completions.create(
        model="gpt-4o-mini",  # TODO: make configurable via env var MODEL_NAME
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ],
        temperature=0,
        max_tokens=64,
    )

    raw = response.choices[0].message.content.strip()
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Name-lookup helper: case-insensitive → title-strip → fuzzy
# ---------------------------------------------------------------------------

def _lookup_individual(name: str, db):
    """Find an Individual by name with three fallback tiers.

    1. Exact case-insensitive match (ilike).
    2. Fuzzy match against all stored names using difflib (cutoff 0.8).

    Returns ``(individual, matched_name)`` where *matched_name* is what was
    actually found, or ``(None, name)`` if nothing matched.

    Note: honorific handling (Mr./Dr./etc.) is intentionally delegated to the
    OpenAI prompt extraction step rather than implemented locally.
    """
    from app.models.family import Individual

    # Tier 1 – exact, case-insensitive
    person = db.query(Individual).filter(Individual.name.ilike(name)).first()
    if person:
        return person, person.name

    # Tier 2 – fuzzy match against every name in the DB
    # TODO: for large trees replace difflib with a proper edit-distance index
    #       (e.g. pg_trgm on PostgreSQL, or a pre-built Levenshtein index).
    all_people = db.query(Individual).all()
    name_map = {p.name.lower(): p for p in all_people}
    candidates = list(name_map.keys())
    close = difflib.get_close_matches(
        name.lower(), candidates, n=1, cutoff=_FUZZY_CUTOFF
    )
    if close:
        person = name_map[close[0]]
        return person, person.name

    return None, name


def answer_kinship_query(query: str, db: Session) -> dict:
    """Parse *query* with OpenAI then resolve the result via the kinship engine.

    Returns a dict::

        {
          "query": <original query>,
          "subject_name": <name extracted from query>,
          "subject_id": <Individual.id or None>,
          "relationship_asked": <term from query or None>,
          "answer": <human-readable answer string>,
        }

    The ``db`` session is required to look up individuals and infer
    relationships.  The caller (API handler) is responsible for providing it.
    """
    from app.models.family import Individual
    from app.services.kinship import infer_relationship, infer_shona_kinship

    intent = _parse_intent(query)
    subject_name: Optional[str] = intent.get("subject_name")
    relative_name: Optional[str] = intent.get("relative_name")
    relationship_asked: Optional[str] = intent.get("relationship_asked")

    if not subject_name:
        return {
            "query": query,
            "subject_name": None,
            "subject_id": None,
            "relationship_asked": relationship_asked,
            "answer": "Could not identify a person name in your question.",
        }

    subject, matched_subject = _lookup_individual(subject_name, db)

    if subject is None:
        return {
            "query": query,
            "subject_name": subject_name,
            "subject_id": None,
            "relationship_asked": relationship_asked,
            "answer": f"No person named '{subject_name}' was found in the family tree.",
        }

    # Two-name query: "who is X to Y?" or "who is X to Y's mother?"
    if relative_name:
        relative, matched_relative = _lookup_individual(relative_name, db)
        if relative is None:
            return {
                "query": query,
                "subject_name": matched_subject,
                "subject_id": subject.id,
                "relationship_asked": relationship_asked,
                "answer": f"No person named '{relative_name}' was found in the family tree.",
            }

        # If the query asks through an intermediate chain such as "Tonya's mother",
        # first resolve that intermediate from subject (Tonya -> mother -> Fadzi),
        # then compute relative's relationship to the intermediate (Willie -> Fadzi).
        if relationship_asked:
            all_individuals = db.query(Individual).filter(Individual.id != subject.id).all()
            intermediates = []
            for person in all_individuals:
                rel_from_subject = infer_relationship(db, subject.id, person.id)
                if rel_from_subject.lower() == relationship_asked.lower():
                    intermediates.append(person)

            if intermediates:
                resolved_answers = []
                for anchor in intermediates:
                    eng = infer_relationship(db, anchor.id, relative.id)
                    shona = infer_shona_kinship(db, anchor.id, relative.id)
                    resolved_answers.append(f"{matched_relative} is {anchor.name}'s {eng} ({shona}).")

                answer = " ".join(resolved_answers)
                return {
                    "query": query,
                    "subject_name": matched_subject,
                    "subject_id": subject.id,
                    "relationship_asked": relationship_asked,
                    "answer": answer,
                }

        # Fallback: no intermediate relation requested/found, answer directly from subject.
        eng = infer_relationship(db, subject.id, relative.id)
        shona = infer_shona_kinship(db, subject.id, relative.id)
        answer = f"{matched_relative} is {matched_subject}'s {eng} ({shona})."
        return {
            "query": query,
            "subject_name": matched_subject,
            "subject_id": subject.id,
            "relationship_asked": relationship_asked,
            "answer": answer,
        }

    # Single-name query: find all relatives (or those matching relationship_asked).
    all_individuals = db.query(Individual).filter(Individual.id != subject.id).all()

    matches = []
    for person in all_individuals:
        eng = infer_relationship(db, subject.id, person.id)
        shona = infer_shona_kinship(db, subject.id, person.id)
        if relationship_asked is None or eng.lower() == relationship_asked.lower():
            matches.append(f"{person.name} ({eng} / {shona})")

    if not matches:
        rel_desc = f"'{relationship_asked}'" if relationship_asked else "any known relative"
        answer = f"{matched_subject} has no {rel_desc} recorded in the family tree."
    elif relationship_asked:
        answer = f"{matched_subject}'s {relationship_asked}: {', '.join(matches)}."
    else:
        answer = f"Known relatives of {matched_subject}: {', '.join(matches)}."

    return {
        "query": query,
        "subject_name": matched_subject,
        "subject_id": subject.id,
        "relationship_asked": relationship_asked,
        "answer": answer,
    }
