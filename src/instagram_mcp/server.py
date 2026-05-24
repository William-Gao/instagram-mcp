from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import FBGraphClient, InstagramAPIError, InstagramClient
from .config import Config

logger = logging.getLogger(__name__)


mcp = FastMCP("instagram-mcp")

_client: InstagramClient | None = None
_fb_client: FBGraphClient | None = None
_config: Config | None = None


def get_client() -> InstagramClient:
    global _client, _config
    if _client is None:
        _config = Config.from_env()
        _client = InstagramClient(_config)
    return _client


def get_fb_client() -> FBGraphClient | None:
    """Return a Facebook Graph API client if INSTAGRAM_FB_ACCESS_TOKEN is set, else None."""
    global _fb_client, _config
    if _config is None:
        get_client()
    assert _config is not None
    if not _config.has_fb_graph:
        return None
    if _fb_client is None:
        _fb_client = FBGraphClient(_config)
    return _fb_client


def get_config() -> Config:
    if _config is None:
        get_client()
    assert _config is not None
    return _config


def fb_required_error(feature: str) -> dict[str, Any]:
    return {
        "ok": False,
        "error": {
            "message": (
                f"{feature} requires Facebook Graph API access. Set "
                "INSTAGRAM_FB_ACCESS_TOKEN (EAA-prefixed Page access token) and "
                "INSTAGRAM_FB_IG_USER_ID (your IG Business Account ID) in your env. "
                "Call the `discover_fb_setup` tool with just the FB token to "
                "auto-find your IG Business Account ID. Full setup guide in the README."
            ),
            "type": "FBGraphTokenMissing",
        },
    }


def format_error(e: Exception) -> dict[str, Any]:
    if isinstance(e, InstagramAPIError):
        return {"ok": False, "error": e.to_dict()}
    return {"ok": False, "error": {"message": str(e), "type": type(e).__name__}}


@asynccontextmanager
async def safe_call():
    try:
        yield
    except InstagramAPIError as e:
        logger.warning("Instagram API error: %s", e)
        raise


# Trigger tool registrations from sub-modules
from .tools import (  # noqa: E402,F401
    auth,
    comments,
    discovery,
    hashtags,
    insights,
    media,
    messaging,
    publish,
)
