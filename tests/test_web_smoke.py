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

from starlette.testclient import TestClient  # noqa: E402  # isort: skip

from reasoning_core.web.server import app  # noqa: E402  # isort: skip


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
