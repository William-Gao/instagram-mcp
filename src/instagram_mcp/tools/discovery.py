from __future__ import annotations

from typing import Any

from ..server import mcp


@mcp.tool()
async def business_discovery(
    target_username: str,
    include_media: bool = True,
    media_limit: int = 10,
) -> dict[str, Any]:
    """Look up a public Business or Creator account's profile.

    NOTE: This endpoint is only available via the Facebook Graph API path
    (graph.facebook.com), which requires linking your Instagram account to a
    Facebook Page. It is NOT available via the Instagram Login API used by this
    server. Call will return a structured error explaining this.

    Args:
        target_username: Instagram username to inspect (without "@").
        include_media: Whether to include the target's recent media.
        media_limit: Number of recent media items to include (1-50, default 10).
    """
    return {
        "ok": False,
        "error": {
            "message": (
                "business_discovery is not available via the Instagram Login API "
                "(graph.instagram.com). This endpoint requires the Facebook Graph "
                "API path (graph.facebook.com) with a Facebook Page linked. "
                "Consider using a public web scraping approach or linking your IG "
                "to a Facebook Page if you need this functionality."
            ),
            "type": "UnsupportedByInstagramLoginAPI",
            "target_username": target_username.lstrip("@"),
        },
    }
