"""Web interface for reasoning-core.

Importing this package does not import the FastAPI application, so the core
library stays importable without the optional ``web`` dependencies. Use
``from reasoning_core.web import app`` (requires ``pip install
"reasoning-core[web]"``) to access the application.
"""

__all__ = ["app"]


def __getattr__(name):
    """Lazily expose the FastAPI app (PEP 562)."""
    if name == "app":
        from reasoning_core.web.server import app

        return app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
