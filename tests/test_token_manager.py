"""Tests for instagram_mcp.token_manager (mocked Meta responses via respx).

We can't fast-forward real 60-day clocks, so expiry/refresh behaviour is exercised
with mocked HTTP + injected timestamps.
"""
from __future__ import annotations

from datetime import timedelta

import httpx
import pytest
import respx

from instagram_mcp import token_manager as tm

IG_REFRESH_URL = "https://graph.instagram.com/refresh_access_token"
FB_DEBUG_URL = "https://graph.facebook.com/v23.0/debug_token"


@pytest.fixture
def base_env(monkeypatch, tmp_path):
    """Isolate Config from the real repo .env and give a clean writable temp .env."""
    env_file = tmp_path / ".env"
    env_file.write_text("")
    monkeypatch.setattr("instagram_mcp.config.ENV_PATH", env_file)
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "OLDIGAA")
    monkeypatch.delenv("INSTAGRAM_ACCESS_TOKEN_REFRESHED_AT", raising=False)
    monkeypatch.delenv("INSTAGRAM_ACCESS_TOKEN_EXPIRES_AT", raising=False)
    monkeypatch.delenv("INSTAGRAM_FB_ACCESS_TOKEN", raising=False)
    return env_file


def test_should_refresh_logic():
    now = tm._now()
    # < 24h old -> never refresh
    assert tm.should_refresh(now, now - timedelta(hours=1), None) is False
    # old enough, expiry unknown -> refresh (safe default)
    assert tm.should_refresh(now, now - timedelta(days=30), None) is True
    # within the refresh window -> refresh
    assert tm.should_refresh(now, now - timedelta(days=30), now + timedelta(days=5)) is True
    # plenty of runway left -> don't refresh
    assert tm.should_refresh(now, now - timedelta(days=2), now + timedelta(days=50)) is False


@respx.mock
async def test_refresh_igaa_success_persists(base_env):
    respx.get(IG_REFRESH_URL).mock(
        return_value=httpx.Response(200, json={"access_token": "NEWIGAA", "expires_in": 5184000})
    )
    res = await tm.refresh_igaa(env_path=base_env, force=True)
    assert res["refreshed"] is True
    assert res["needs_reauth"] is False
    assert res["expires_in"] == 5184000
    assert res["token_tail"] == "EWIGAA"
    written = base_env.read_text()
    assert "INSTAGRAM_ACCESS_TOKEN=NEWIGAA" in written
    assert "INSTAGRAM_ACCESS_TOKEN_EXPIRES_AT=" in written
    assert "INSTAGRAM_ACCESS_TOKEN_REFRESHED_AT=" in written


async def test_refresh_igaa_skips_when_young(base_env, monkeypatch):
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN_REFRESHED_AT", tm._now().isoformat())
    res = await tm.refresh_igaa(env_path=base_env)  # force=False
    assert res["refreshed"] is False
    assert res["needs_reauth"] is False
    assert "24h" in res["reason"]
    # nothing written
    assert "NEWIGAA" not in base_env.read_text()


@respx.mock
async def test_refresh_igaa_dead_token_needs_reauth(base_env):
    respx.get(IG_REFRESH_URL).mock(
        return_value=httpx.Response(
            400,
            json={"error": {"message": "Error validating access token: Session has expired", "code": 190}},
        )
    )
    res = await tm.refresh_igaa(env_path=base_env, force=True)
    assert res["refreshed"] is False
    assert res["needs_reauth"] is True
    assert "interactive" in res["reason"].lower()


@respx.mock
async def test_check_fb_never_expires(base_env, monkeypatch):
    monkeypatch.setenv("INSTAGRAM_FB_ACCESS_TOKEN", "EAAPAGE")
    monkeypatch.setenv("INSTAGRAM_APP_ID", "111")
    monkeypatch.setenv("INSTAGRAM_APP_SECRET", "222")
    respx.get(FB_DEBUG_URL).mock(
        return_value=httpx.Response(
            200,
            json={"data": {"is_valid": True, "expires_at": 0, "data_access_expires_at": 1789936594}},
        )
    )
    res = await tm.check_fb()
    assert res["ok"] is True
    assert res["never_expires"] is True
    assert res["needs_reauth"] is False


async def test_check_fb_not_configured(base_env):
    res = await tm.check_fb()
    assert res["ok"] is False
    assert res["configured"] is False


@respx.mock
async def test_run_flags_attention_on_dead_igaa(base_env, monkeypatch):
    monkeypatch.setenv("INSTAGRAM_FB_ACCESS_TOKEN", "EAAPAGE")
    respx.get(IG_REFRESH_URL).mock(
        return_value=httpx.Response(400, json={"error": {"message": "expired", "code": 190}})
    )
    respx.get(FB_DEBUG_URL).mock(
        return_value=httpx.Response(200, json={"data": {"is_valid": True, "expires_at": 0}})
    )
    res = await tm.run(force=True)
    assert res["needs_attention"] is True
    assert res["igaa"]["needs_reauth"] is True
    assert res["fb"]["ok"] is True
