"""Token lifecycle management for the Instagram MCP.

Refreshes the long-lived IGAA token before it expires and reports Facebook
Page-token health, persisting results back to the repo `.env` (the single source
of truth — see config.ENV_PATH).

IMPORTANT — what this can and cannot do:
  * It CAN refresh an IGAA token that is still valid and >= 24h old (extends 60d),
    and it CAN report FB token validity / data-access expiry.
  * It CANNOT revive a token that has fully expired or been invalidated. Meta
    requires an interactive (browser) re-authorization in that case. When detected,
    the result carries ``needs_reauth: True`` rather than silently "succeeding".

Run on a schedule:  python -m instagram_mcp.token_manager [--force]
Exit code 2 signals "human attention required" (a token is dead / needs re-auth).
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from dotenv import set_key

from .client import FBGraphClient, InstagramAPIError, InstagramClient
from .config import ENV_PATH, Config

# IG refuses to refresh a long-lived token younger than 24h.
MIN_REFRESH_AGE = timedelta(hours=24)
# Refresh when the token is within this window of expiry (used by should_refresh).
REFRESH_WINDOW = timedelta(days=10)
# Meta error code 190 == access token expired / invalidated.
TOKEN_DEAD_CODE = 190


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _persist(env_path: Path | str, **kv: Any) -> None:
    path = Path(env_path)
    if not path.exists():
        path.write_text("")
    for key, val in kv.items():
        if val is not None:
            set_key(str(path), key, str(val), quote_mode="never")


def should_refresh(now: datetime, refreshed_at: datetime | None, expires_at: datetime | None) -> bool:
    """Decide whether an IGAA refresh is due.

    Skip if the token is younger than 24h (IG would reject it). Otherwise refresh
    when we're inside REFRESH_WINDOW of expiry, or when expiry is unknown (safe
    default: refreshing an older-but-valid token simply extends it again).
    """
    if refreshed_at and (now - refreshed_at) < MIN_REFRESH_AGE:
        return False
    if expires_at is None:
        return True
    return (expires_at - now) <= REFRESH_WINDOW


async def refresh_igaa(
    config: Config | None = None,
    *,
    env_path: Path | str = ENV_PATH,
    force: bool = False,
    write: bool = True,
) -> dict[str, Any]:
    """Refresh the long-lived IGAA token and persist it to .env.

    Returns a status dict; never raises for ordinary API failures. ``needs_reauth``
    is True when the token is dead and only an interactive login can fix it.
    """
    config = config or Config.from_env()
    now = _now()
    refreshed_at = _parse_dt(os.environ.get("INSTAGRAM_ACCESS_TOKEN_REFRESHED_AT"))
    expires_at = _parse_dt(os.environ.get("INSTAGRAM_ACCESS_TOKEN_EXPIRES_AT"))

    if not force and not should_refresh(now, refreshed_at, expires_at):
        if refreshed_at and (now - refreshed_at) < MIN_REFRESH_AGE:
            reason = "token <24h old; Instagram refuses refresh until 24h"
        else:
            reason = "not within refresh window yet"
        return {"refreshed": False, "needs_reauth": False, "reason": reason,
                "expires_at": expires_at.isoformat() if expires_at else None}

    async with InstagramClient(config) as client:
        try:
            data = await client.get(
                "refresh_access_token", params={"grant_type": "ig_refresh_token"}
            )
        except InstagramAPIError as e:
            dead = e.code == TOKEN_DEAD_CODE
            return {
                "refreshed": False,
                "needs_reauth": dead,
                "reason": (
                    "IGAA token expired/invalid — an interactive Instagram login is required"
                    if dead
                    else f"refresh failed: {e}"
                ),
                "error": e.to_dict(),
            }

    new_token = data.get("access_token")
    if not new_token:
        return {"refreshed": False, "needs_reauth": True,
                "reason": "refresh returned no access_token", "raw": data}
    expires_in = data.get("expires_in")
    new_expires_at = now + timedelta(seconds=int(expires_in)) if expires_in else None
    if write:
        _persist(
            env_path,
            INSTAGRAM_ACCESS_TOKEN=new_token,
            INSTAGRAM_ACCESS_TOKEN_REFRESHED_AT=now.isoformat(),
            INSTAGRAM_ACCESS_TOKEN_EXPIRES_AT=new_expires_at.isoformat() if new_expires_at else None,
        )
    return {
        "refreshed": True,
        "needs_reauth": False,
        "expires_in": expires_in,
        "expires_at": new_expires_at.isoformat() if new_expires_at else None,
        "token_tail": new_token[-6:],
        "persisted": write,
    }


async def check_fb(config: Config | None = None) -> dict[str, Any]:
    """Report Facebook Page-token health via debug_token (no refresh — Page tokens
    don't expire, but data access lapses ~90 days and then needs re-auth)."""
    config = config or Config.from_env()
    if not config.fb_access_token:
        return {"ok": False, "configured": False, "reason": "no FB token configured"}
    app_token = (
        f"{config.app_id}|{config.app_secret}"
        if config.app_id and config.app_secret
        else config.fb_access_token
    )
    async with FBGraphClient(config) as fb:
        try:
            data = (
                await fb.get(
                    "debug_token",
                    params={"input_token": config.fb_access_token, "access_token": app_token},
                )
            ).get("data", {})
        except InstagramAPIError as e:
            return {"ok": False, "configured": True, "needs_reauth": e.code == TOKEN_DEAD_CODE,
                    "reason": f"debug_token failed: {e}", "error": e.to_dict()}
    expires_at = data.get("expires_at")
    dae = data.get("data_access_expires_at")
    is_valid = data.get("is_valid")
    return {
        "ok": True,
        "configured": True,
        "is_valid": is_valid,
        "never_expires": expires_at == 0,
        "expires_at": expires_at,
        "data_access_expires_at": dae,
        "needs_reauth": not is_valid,
    }


async def run(*, force: bool = False) -> dict[str, Any]:
    """Refresh the IGAA token (if due) and report FB health. Designed for a scheduler."""
    config = Config.from_env()
    igaa = await refresh_igaa(config, force=force)
    fb = await check_fb(config)
    needs_attention = bool(igaa.get("needs_reauth")) or bool(fb.get("needs_reauth"))
    return {"timestamp": _now().isoformat(), "igaa": igaa, "fb": fb,
            "needs_attention": needs_attention}


def main() -> None:
    report = asyncio.run(run(force="--force" in sys.argv))
    print(json.dumps(report, indent=2))
    sys.exit(2 if report.get("needs_attention") else 0)


if __name__ == "__main__":
    main()
