"""Safety tests for the web upload-directory cleanup.

The web layer previously defaulted ``UPLOAD_DIR`` to the current working
directory: ``Path("")`` is ``Path(".")`` and Path objects are always truthy,
so the intended temp-directory fallback never ran. Because the server
registers an ``atexit`` cleanup that deletes old files, merely importing the
web server in a process started from a checkout would delete top-level files
in that directory. These tests pin the fix: a dedicated default directory and
guards that keep cleanup away from working directories and repositories.

Skipped automatically when the optional ``web`` dependencies are not
installed (``pip install -e ".[web]"``).
"""

import os
import time
from pathlib import Path

import pytest

pytest.importorskip("fastapi", reason="web extras not installed")

from reasoning_core.web import server  # noqa: E402  # isort: skip


def _make_old(path: Path, age_seconds: float = 7200) -> None:
    """Backdate a file's mtime so it counts as old."""
    old = time.time() - age_seconds
    os.utime(path, (old, old))


def test_default_upload_dir_is_not_the_working_directory():
    """The default upload directory must never be whatever cwd the process has."""
    from reasoning_core.web.config import UPLOAD_DIR

    if not os.getenv("REASONING_CORE_UPLOAD_DIR", "").strip():
        assert UPLOAD_DIR.name == "reasoning_core_uploads"
    assert UPLOAD_DIR.resolve() != Path.cwd().resolve()


def test_cleanup_refuses_repository_working_tree(tmp_path, monkeypatch):
    """A directory that looks like a repository working tree is left alone."""
    (tmp_path / ".git").mkdir()
    victim = tmp_path / "IMPORTANT.md"
    victim.write_text("do not delete")
    _make_old(victim)

    monkeypatch.setattr(server, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(server, "FILE_MAX_AGE_SECONDS", 3600)

    server.cleanup_old_files()

    assert victim.exists()


def test_cleanup_refuses_the_working_directory(tmp_path, monkeypatch):
    """Even without .git, the process working directory is never cleaned."""
    workdir = tmp_path / "workdir"
    workdir.mkdir()
    victim = workdir / "IMPORTANT.md"
    victim.write_text("do not delete")
    _make_old(victim)

    monkeypatch.chdir(workdir)
    monkeypatch.setattr(server, "UPLOAD_DIR", workdir)
    monkeypatch.setattr(server, "FILE_MAX_AGE_SECONDS", 3600)

    server.cleanup_old_files()

    assert victim.exists()


def test_cleanup_removes_old_files_from_dedicated_upload_dir(tmp_path, monkeypatch):
    """Cleanup still works for a dedicated (non-repository) upload directory."""
    old_file = tmp_path / "task_1_old.pdf"
    new_file = tmp_path / "task_2_new.pdf"
    old_file.write_bytes(b"old")
    new_file.write_bytes(b"new")
    _make_old(old_file)

    monkeypatch.setattr(server, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(server, "FILE_MAX_AGE_SECONDS", 3600)

    server.cleanup_old_files()

    assert not old_file.exists()
    assert new_file.exists()
