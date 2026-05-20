from __future__ import annotations

from typing import Any

from ..server import format_error, get_client, mcp


async def _ig_user_id() -> str:
    client = get_client()
    me = await client.get("me", params={"fields": "id"})
    uid = me.get("id")
    if not uid:
        raise RuntimeError("Could not resolve Instagram user id from /me")
    return uid


@mcp.tool()
async def search_hashtag(hashtag: str) -> dict[str, Any]:
    """Look up a hashtag's Instagram ID for use with get_hashtag_media.

    Args:
        hashtag: Hashtag name with or without a leading "#" (max 100 chars).

    Note: Each account is limited to 30 unique hashtag searches in a rolling 7-day window.
    """
    try:
        client = get_client()
        q = hashtag.lstrip("#")
        uid = await _ig_user_id()
        data = await client.get("ig_hashtag_search", params={"user_id": uid, "q": q})
        return {"ok": True, **data}
    except Exception as e:
        return format_error(e)


@mcp.tool()
async def get_hashtag_media(
    hashtag_id: str,
    media_type: str = "top",
    limit: int = 25,
) -> dict[str, Any]:
    """Get top or recent media for a hashtag.

    Args:
        hashtag_id: Hashtag ID from search_hashtag.
        media_type: "top" (most popular) or "recent" (most recent).
        limit: Number of posts to return (1-50, default 25).
    """
    try:
        client = get_client()
        uid = await _ig_user_id()
        endpoint = "top_media" if media_type == "top" else "recent_media"
        data = await client.get(
            f"{hashtag_id}/{endpoint}",
            params={
                "user_id": uid,
                "fields": "id,caption,media_type,permalink,timestamp,like_count,comments_count,media_url",
                "limit": max(1, min(50, limit)),
            },
        )
        return {"ok": True, **data}
    except Exception as e:
        return format_error(e)
