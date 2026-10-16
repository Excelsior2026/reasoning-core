"""Smoke tests for the optional web layer.

The web package previously could not be imported at all: ``reasoning_core.web``
eagerly imported the FastAPI app, which failed on a ``fastapi.middleware.base``
import and on missing typing imports. These tests pin the fix: the server app
must import, build, and serve its core routes.

Skipped automatically when the optional ``web`` dependencies are not
installed (``pip install -e ".[web]"``).
"""

import pytest

pytest.importorskip("fastapi", reason="web extras not installed")

from pydantic import ValidationError  # noqa: E402  # isort: skip
from starlette.testclient import TestClient  # noqa: E402  # isort: skip

from reasoning_core.web.server import app  # noqa: E402  # isort: skip
from reasoning_core.web.validation import URLRequest  # noqa: E402  # isort: skip


def test_app_builds_with_core_routes():
    """Importing the server must produce an app with its core routes."""
    paths = {getattr(route, "path", None) for route in app.routes}
    assert "/api/health" in paths
    assert "/api/analyze/text" in paths
    assert "/api/analyze/file" in paths
    assert "/api/analyze/url" in paths


def test_health_endpoint():
    """The health endpoint responds without authentication."""
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_url_request_accepts_legit_url_forms():
    """URL validation must accept common, legitimate URL shapes (review F-4)."""
    accepted = [
        "https://example.com",
        "https://example.solutions",  # TLD longer than 6 characters
        "https://example.com/path?q=1#frag",  # fragment
        "http://[::1]:8000/",  # IPv6 literal
        "http://localhost:8000",
        "http://127.0.0.1:8000/",
    ]
    for url in accepted:
        assert URLRequest(url=url).url == url


def test_url_request_rejects_non_http_urls():
    """Garbage and non-HTTP schemes must still be rejected."""
    for url in ["not-a-url", "javascript:alert(1)", "ftp://example.com"]:
        with pytest.raises(ValidationError):
            URLRequest(url=url)
