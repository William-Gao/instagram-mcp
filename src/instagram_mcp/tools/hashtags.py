from __future__ import annotations

from typing import Any

from ..server import mcp

_UNSUPPORTED_MSG = (
    "Hashtag search endpoints (ig_hashtag_search, /{hashtag-id}/top_media, "
    "/{hashtag-id}/recent_media) are not available via the Instagram Login API "
    "(graph.instagram.com). They require the Facebook Graph API path "
    "(graph.facebook.com) with a Facebook Page linked to the IG account."
)


@mcp.tool()
async def search_hashtag(hashtag: str) -> dict[str, Any]:
    """Look up a hashtag's Instagram ID.

    NOTE: This endpoint is only available via the Facebook Graph API path,
    which requires a Facebook Page linked to your Instagram account. It is NOT
    available via the Instagram Login API used by this server.

    Args:
        hashtag: Hashtag name with or without a leading "#" (max 100 chars).
    """
    return {
        "ok": False,
        "error": {
            "message": _UNSUPPORTED_MSG,
            "type": "UnsupportedByInstagramLoginAPI",
            "hashtag": hashtag.lstrip("#"),
        },
    }


@mcp.tool()
async def get_hashtag_media(
    hashtag_id: str,
    media_type: str = "top",
    limit: int = 25,
) -> dict[str, Any]:
    """Get top or recent media for a hashtag.

    NOTE: Same limitation as search_hashtag - not available via Instagram Login API.
    """
    return {
        "ok": False,
        "error": {
            "message": _UNSUPPORTED_MSG,
            "type": "UnsupportedByInstagramLoginAPI",
            "hashtag_id": hashtag_id,
        },
    }
