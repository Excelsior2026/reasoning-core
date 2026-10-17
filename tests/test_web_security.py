"""Security regression tests for the optional web layer (issues #4-#8).

Covers:

- authentication enforcement on state-changing endpoints (#4)
- domain id validation / path-traversal prevention (#5)
- SSRF guard: hostname resolution, redirect re-validation, numeric host
  forms (#6)
- local-first defaults: loopback bind and auth-off default (#7)
- pypdf-based PDF parsing after the PyPDF2 migration (#8)

Skipped automatically when the optional ``web`` dependencies are not
installed (``pip install -e ".[web]"``).
"""

import json
import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("fastapi", reason="web extras not installed")

from starlette.testclient import TestClient  # noqa: E402  # isort: skip

from reasoning_core.web import rate_limit, server  # noqa: E402  # isort: skip
from reasoning_core.web.domain_builder import DomainBuilder  # noqa: E402  # isort: skip
from reasoning_core.web.scraper import ScrapingError, is_safe_url, scrape_website  # noqa: E402  # isort: skip

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _disable_rate_limiting(monkeypatch):
    """Keep in-process HTTP tests independent of the rate limiter."""
    monkeypatch.setattr(rate_limit, "RATE_LIMIT_ENABLED", False)


def _run_probe(script: str, extra_env: dict) -> dict:
    """Run a probe script in a fresh interpreter with a clean REASONING_CORE_ env."""
    env = {key: value for key, value in os.environ.items() if not key.startswith("REASONING_CORE_")}
    env.update(extra_env)
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        env=env,
        timeout=180,
    )
    assert result.returncode == 0, f"probe failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    lines = [line for line in result.stdout.splitlines() if line.startswith("{")]
    assert lines, f"no JSON output from probe:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    return json.loads(lines[-1])


# --- #4: authentication enforcement -----------------------------------------

_AUTH_ENFORCEMENT_PROBE = """
import json

from starlette.testclient import TestClient

from reasoning_core.web.auth import create_jwt_token
from reasoning_core.web.server import app

client = TestClient(app)
results = {}
results["clear_no_credentials"] = client.post("/api/cache/clear").status_code
results["clear_bad_key"] = client.post("/api/cache/clear", headers={"X-API-Key": "wrong-key"}).status_code
results["clear_api_key"] = client.post("/api/cache/clear", headers={"X-API-Key": "test-key-123"}).status_code
token = create_jwt_token("probe-user", "probe")
results["clear_jwt"] = client.post("/api/cache/clear", headers={"Authorization": "Bearer " + token}).status_code
results["create_domain_no_credentials"] = client.post(
    "/api/domains", json={"name": "probe", "concept_types": ["x"]}
).status_code
results["test_domain_no_credentials"] = client.post("/api/domains/probe/test?test_text=hi").status_code
results["analyze_text_no_credentials"] = client.post(
    "/api/analyze/text", json={"text": "hello", "domain": "generic"}
).status_code
results["analyze_url_no_credentials"] = client.post(
    "/api/analyze/url", json={"url": "https://example.com/", "domain": "generic"}
).status_code
results["analyze_batch_no_credentials"] = client.post(
    "/api/analyze/batch", json={"items": [{"text": "hello"}], "domain": "generic"}
).status_code
results["analyze_file_no_credentials"] = client.post(
    "/api/analyze/file",
    files={"file": ("probe.txt", b"probe text", "text/plain")},
).status_code
# With a valid key the handler runs; an invalid domain then fails validation
# (400) without processing or storing an upload.
results["analyze_file_with_key"] = client.post(
    "/api/analyze/file",
    files={"file": ("probe.txt", b"probe text", "text/plain")},
    data={"domain": "not-a-domain"},
    headers={"X-API-Key": "test-key-123"},
).status_code
results["delete_domain_no_credentials"] = client.delete(
    "/api/domains/probe-domain-does-not-exist-9f3a"
).status_code
# With a valid key the handler runs; a missing domain returns 404.
results["delete_domain_with_key"] = client.delete(
    "/api/domains/probe-domain-does-not-exist-9f3a", headers={"X-API-Key": "test-key-123"}
).status_code
results["progress_no_credentials"] = client.get("/api/progress/probe-task").status_code
results["health_no_credentials"] = client.get("/api/health").status_code
results["list_domains_no_credentials"] = client.get("/api/domains").status_code
print(json.dumps(results))
"""


def test_auth_enforcement_when_enabled():
    """State-changing endpoints must 401 without credentials when auth is on."""
    results = _run_probe(
        _AUTH_ENFORCEMENT_PROBE,
        {
            "REASONING_CORE_AUTH_ENABLED": "true",
            "REASONING_CORE_API_KEYS": "test-key-123",
            "REASONING_CORE_JWT_SECRET": "probe-secret",
            "REASONING_CORE_RATE_LIMIT_ENABLED": "false",
        },
    )
    assert results["clear_no_credentials"] == 401
    assert results["clear_bad_key"] == 401
    assert results["clear_api_key"] == 200
    assert results["clear_jwt"] == 200
    assert results["create_domain_no_credentials"] == 401
    assert results["test_domain_no_credentials"] == 401
    assert results["analyze_text_no_credentials"] == 401
    assert results["analyze_url_no_credentials"] == 401
    assert results["analyze_batch_no_credentials"] == 401
    assert results["analyze_file_no_credentials"] == 401
    assert results["analyze_file_with_key"] == 400  # auth accepted; domain rejected
    assert results["delete_domain_no_credentials"] == 401
    assert results["delete_domain_with_key"] == 404  # auth accepted; domain missing
    assert results["progress_no_credentials"] == 401
    # Dependency-free / read-only endpoints stay anonymous.
    assert results["health_no_credentials"] == 200
    assert results["list_domains_no_credentials"] == 200


# --- #7: local-first defaults -----------------------------------------------

_DEFAULTS_PROBE = """
import json

from starlette.testclient import TestClient

from reasoning_core.web import config
from reasoning_core.web.server import app

client = TestClient(app)
results = {
    "auth_enabled_default": config.AUTH_ENABLED,
    "host_default": config.HOST,
    "port_default": config.PORT,
    "clear_no_credentials": client.post("/api/cache/clear").status_code,
}
print(json.dumps(results))
"""


def test_local_first_defaults():
    """Defaults: loopback bind, authentication off, local requests allowed."""
    results = _run_probe(_DEFAULTS_PROBE, {"REASONING_CORE_RATE_LIMIT_ENABLED": "false"})
    assert results["auth_enabled_default"] is False
    assert results["host_default"] == "127.0.0.1"
    assert results["port_default"] == 8000
    assert results["clear_no_credentials"] == 200


# --- #5: domain id validation -----------------------------------------------


def _domain_config(**overrides):
    config = {"name": "Test Domain", "concept_types": ["concepts"]}
    config.update(overrides)
    return config


def test_domain_builder_rejects_invalid_ids(tmp_path):
    """Traversal-shaped ids must never reach the filesystem."""
    builder = DomainBuilder(tmp_path)
    invalid_ids = ["../evil", "..", "a/b", "a\\b", "a.b", "", " ", "x" * 65, "%2e%2e"]
    for invalid_id in invalid_ids:
        with pytest.raises(ValueError):
            builder.save_domain(_domain_config(id=invalid_id))
        with pytest.raises(ValueError):
            builder.load_domain(invalid_id)
        with pytest.raises(ValueError):
            builder.delete_domain(invalid_id)
    assert list(tmp_path.iterdir()) == []


def test_domain_builder_accepts_valid_ids_and_generates_safe_ids(tmp_path):
    """Valid ids round-trip; generated ids from arbitrary names stay valid."""
    builder = DomainBuilder(tmp_path)
    assert builder.save_domain(_domain_config(id="my_domain-1")) == "my_domain-1"
    assert (tmp_path / "my_domain-1.json").exists()

    generated = builder.save_domain(_domain_config(name="Weird/Name.Idea! (v2)"))
    assert builder.load_domain(generated)["name"] == "Weird/Name.Idea! (v2)"
    assert (tmp_path / f"{generated}.json").exists()

    assert builder.delete_domain("my_domain-1") is True
    assert not (tmp_path / "my_domain-1.json").exists()


def test_domain_api_rejects_traversal_and_round_trips(tmp_path, monkeypatch):
    """The domains API validates ids before touching the filesystem."""
    local_builder = DomainBuilder(tmp_path)
    monkeypatch.setattr(server, "get_domain_builder", lambda: local_builder)
    client = TestClient(server.app)

    response = client.post("/api/domains", json=_domain_config(id="../../evil"))
    assert response.status_code == 400
    assert not list(tmp_path.iterdir())

    response = client.post("/api/domains", json=_domain_config(id="api_domain-1"))
    assert response.status_code == 200
    assert response.json()["id"] == "api_domain-1"
    assert (tmp_path / "api_domain-1.json").exists()

    assert client.get("/api/domains/api_domain-1").status_code == 200
    assert client.get("/api/domains/...").status_code == 404
    assert client.delete("/api/domains/api_domain-1").status_code == 200
    assert not (tmp_path / "api_domain-1.json").exists()


# --- #6: SSRF guard ----------------------------------------------------------


def test_ssrf_blocks_private_and_obfuscated_literals():
    """Private targets are rejected."""
    blocked = [
        "http://127.0.0.1/",
        "http://127.0.0.1:8000/",
        "http://[::1]/",
        "http://[::1]:8000/",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.1/",
        "http://192.168.1.1/",
        "http://0.0.0.0/",
        "http://[::ffff:127.0.0.1]/",  # IPv4-mapped loopback
    ]
    for url in blocked:
        assert is_safe_url(url) is False, url


def test_ssrf_rejects_legacy_numeric_host_spellings():
    """Legacy numeric spellings are rejected outright (review round 1, F-1).

    The platform resolver may read these differently from any local parsing
    (e.g. ``010.0.0.1``: octal for ``inet_aton``, decimal for the darwin and
    glibc resolvers), so the guard refuses to guess and rejects them all.
    """
    rejected = [
        "http://2130706433/",  # decimal integer
        "http://0x7f000001/",  # hex
        "http://0177.0.0.1/",  # leading zero
        "http://010.0.0.1/",  # resolver reads 10.0.0.1
        "http://0127.0.0.1/",  # resolver reads 127.0.0.1
        "http://0172.16.0.1/",  # resolver reads 172.16.0.1
        "http://127.1/",  # shortened
    ]
    for url in rejected:
        assert is_safe_url(url) is False, url


def test_ssrf_allows_public_literals():
    """Public addresses and ordinary URL shapes remain allowed."""
    assert is_safe_url("http://93.184.216.34/") is True
    assert is_safe_url("https://93.184.216.34:8443/page?q=1") is True


def test_ssrf_rejects_non_http_schemes():
    """Non-HTTP(S) URLs are never fetchable."""
    for url in ["ftp://93.184.216.34/", "file:///etc/passwd", "javascript:alert(1)", "not-a-url"]:
        assert is_safe_url(url) is False


def test_ssrf_rejects_private_dns_answers(monkeypatch):
    """Hostnames are resolved; any private answer blocks the URL."""

    def fake_getaddrinfo(host, port, *args, **kwargs):
        if host == "public.example.com":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]
        if host == "mixed.example.com":
            return [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0)),
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", 0)),
            ]
        if host == "mapped.example.com":
            return [(socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("::ffff:169.254.169.254", 0, 0, 0))]
        raise socket.gaierror("Name or service not known")

    monkeypatch.setattr("reasoning_core.web.scraper.socket.getaddrinfo", fake_getaddrinfo)

    assert is_safe_url("https://public.example.com/page") is True
    assert is_safe_url("https://mixed.example.com/") is False
    assert is_safe_url("https://mapped.example.com/") is False
    assert is_safe_url("https://nxdomain.example.com/") is False


class _FakeResponse:
    """Minimal stand-in for a requests.Response."""

    def __init__(self, status_code, headers=None, content=b"", url=""):
        self.status_code = status_code
        self.headers = headers or {}
        self.content = content
        self.url = url

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_scrape_rejects_private_redirect_target(monkeypatch):
    """Redirects must be re-validated before being followed."""
    calls = []

    def fake_get(url, **kwargs):
        calls.append({"url": url, "allow_redirects": kwargs.get("allow_redirects")})
        return _FakeResponse(302, {"location": "http://169.254.169.254/latest/meta-data/"}, url=url)

    monkeypatch.setattr("requests.get", fake_get)

    with pytest.raises(ScrapingError):
        scrape_website("https://93.184.216.34/")

    assert len(calls) == 1
    assert calls[0]["allow_redirects"] is False


def test_scrape_rejects_obfuscated_redirect_target(monkeypatch):
    """Obfuscated numeric redirect targets are blocked too."""
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        return _FakeResponse(302, {"location": "http://2130706433/"}, url=url)

    monkeypatch.setattr("requests.get", fake_get)

    with pytest.raises(ScrapingError):
        scrape_website("https://93.184.216.34/")

    assert calls == ["https://93.184.216.34/"]


def test_scrape_rejects_leading_zero_redirect_target(monkeypatch):
    """Leading-zero redirect targets are rejected (review round 1, F-1).

    On this platform the resolver reads ``0127.0.0.1`` as 127.0.0.1, so the
    hop must be refused before any request is made to it.
    """
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        return _FakeResponse(302, {"location": "http://0127.0.0.1:8080/latest/meta-data/"}, url=url)

    monkeypatch.setattr("requests.get", fake_get)

    with pytest.raises(ScrapingError):
        scrape_website("https://93.184.216.34/")

    assert calls == ["https://93.184.216.34/"]


def test_scrape_follows_validated_redirects(monkeypatch):
    """Safe redirects (including relative Location values) are followed."""
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        if url == "https://93.184.216.34/start":
            return _FakeResponse(302, {"location": "/final-page"}, url=url)
        return _FakeResponse(200, content=b"<html><body><p>Hello redirect world</p></body></html>", url=url)

    monkeypatch.setattr("requests.get", fake_get)

    result = scrape_website("https://93.184.216.34/start")

    assert calls == ["https://93.184.216.34/start", "https://93.184.216.34/final-page"]
    assert "Hello redirect world" in result["text"]


def test_scrape_rejects_private_initial_url():
    """A private initial URL fails before any request is made."""
    with pytest.raises(ScrapingError):
        scrape_website("http://169.254.169.254/")


def test_scrape_rejects_too_many_redirects(monkeypatch):
    """Redirect loops are bounded."""

    def fake_get(url, **kwargs):
        return _FakeResponse(302, {"location": "/loop"}, url=url)

    monkeypatch.setattr("requests.get", fake_get)

    with pytest.raises(ScrapingError):
        scrape_website("https://93.184.216.34/loop")


# --- #8: PyPDF2 -> pypdf migration -------------------------------------------


def test_pdf_parsing_uses_pypdf(tmp_path):
    """PDF text extraction still works after the pypdf migration."""
    pytest.importorskip("reportlab")
    from reportlab.pdfgen import canvas as pdf_canvas

    from reasoning_core.web.parsers import parse_document

    pdf_path = tmp_path / "sample.pdf"
    pdf = pdf_canvas.Canvas(str(pdf_path))
    pdf.drawString(72, 720, "Hello reasoning core")
    pdf.save()

    result = parse_document(str(pdf_path))
    assert "Hello reasoning core" in result["text"]
