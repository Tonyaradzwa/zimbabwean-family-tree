import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app

# TestClient raises_server_exceptions=False so CORS headers are still inspectable
client = TestClient(app, raise_server_exceptions=False)

VITE_ORIGIN = "http://localhost:5173"
UNKNOWN_ORIGIN = "http://evil.example.com"


def test_cors_preflight_allowed_origin():
    """OPTIONS preflight from the Vite dev server should be approved."""
    resp = client.options(
        "/api/v1/individuals/",
        headers={
            "Origin": VITE_ORIGIN,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == VITE_ORIGIN
    assert "GET" in resp.headers.get("access-control-allow-methods", "").upper()


def test_cors_actual_request_allowed_origin():
    """A real GET from the allowed origin carries the ACAO header."""
    resp = client.get(
        "/api/v1/individuals/",
        headers={"Origin": VITE_ORIGIN},
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == VITE_ORIGIN


def test_cors_disallowed_origin():
    """An origin not in allow_origins must NOT receive the ACAO header."""
    resp = client.get(
        "/api/v1/individuals/",
        headers={"Origin": UNKNOWN_ORIGIN},
    )
    assert resp.headers.get("access-control-allow-origin") != UNKNOWN_ORIGIN
