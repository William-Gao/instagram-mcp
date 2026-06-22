"""Shared pytest fixtures for the tool tests."""
from __future__ import annotations

import pytest


@pytest.fixture
def env(monkeypatch, tmp_path):
    """Hermetic env: no real .env, fresh server-global clients, test tokens."""
    import instagram_mcp.server as srv
    monkeypatch.setattr("instagram_mcp.config.ENV_PATH", tmp_path / ".env")
    monkeypatch.setattr("instagram_mcp.config.load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "IGTOK")
    monkeypatch.setenv("INSTAGRAM_FB_ACCESS_TOKEN", "EAATOK")
    monkeypatch.setenv("INSTAGRAM_FB_IG_USER_ID", "999")
    srv._client = srv._fb_client = srv._config = None
    yield
    srv._client = srv._fb_client = srv._config = None
