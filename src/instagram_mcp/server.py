from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import InstagramAPIError, InstagramClient
from .config import Config

logger = logging.getLogger(__name__)


mcp = FastMCP("instagram-mcp")

_client: InstagramClient | None = None
_config: Config | None = None


def get_client() -> InstagramClient:
    global _client, _config
    if _client is None:
        _config = Config.from_env()
        _client = InstagramClient(_config)
    return _client


def get_config() -> Config:
    if _config is None:
        get_client()
    assert _config is not None
    return _config


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
