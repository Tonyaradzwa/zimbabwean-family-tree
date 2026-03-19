import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app

# TestClient raises_server_exceptions=False so CORS headers are still inspectable
client = TestClient(app, raise_server_exceptions=False)

VITE_ORIGIN = "http://localhost:5173"
VITE_ALT_ORIGIN = "http://localhost:5175"
FORWARDED_ORIGIN = "https://congenial-goldfish-9gjr4r94v62pv9q-5175.app.github.dev"
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
        "/",
        headers={"Origin": VITE_ORIGIN},
        follow_redirects=False,
    )
    assert resp.status_code in (307, 308)
    assert resp.headers.get("access-control-allow-origin") == VITE_ORIGIN


def test_cors_preflight_allowed_alt_localhost_port():
    """OPTIONS preflight from an alternate local Vite port is approved."""
    resp = client.options(
        "/api/v1/individuals/",
        headers={
            "Origin": VITE_ALT_ORIGIN,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == VITE_ALT_ORIGIN


def test_cors_preflight_allowed_codespaces_forwarded_origin():
    """OPTIONS preflight from a Codespaces forwarded frontend URL is approved."""
    resp = client.options(
        "/api/v1/individuals/",
        headers={
            "Origin": FORWARDED_ORIGIN,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == FORWARDED_ORIGIN


def test_cors_disallowed_origin():
    """An origin not in allow_origins must NOT receive the ACAO header."""
    resp = client.get(
        "/api/v1/individuals/",
        headers={"Origin": UNKNOWN_ORIGIN},
    )
    assert resp.headers.get("access-control-allow-origin") != UNKNOWN_ORIGIN
