from __future__ import annotations

from typing import Any

from ..server import format_error, get_client, mcp


@mcp.tool()
async def business_discovery(
    target_username: str,
    include_media: bool = True,
    media_limit: int = 10,
) -> dict[str, Any]:
    """Look up a public Business or Creator account's profile (and optionally recent media).

    Args:
        target_username: Instagram username to inspect (without "@").
        include_media: Whether to include the target's recent media.
        media_limit: Number of recent media items to include (1-50, default 10).
    """
    try:
        client = get_client()
        username = target_username.lstrip("@")
        base = (
            "id,username,name,biography,profile_picture_url,website,"
            "followers_count,follows_count,media_count"
        )
        if include_media:
            limit = max(1, min(50, media_limit))
            media = (
                ".media.limit("
                + str(limit)
                + "){id,caption,media_type,permalink,timestamp,like_count,comments_count,media_url}"
            )
            fields = f"business_discovery.username({username}){{{base}{media}}}"
        else:
            fields = f"business_discovery.username({username}){{{base}}}"
        data = await client.get("me", params={"fields": fields})
        return {"ok": True, **data}
    except Exception as e:
        return format_error(e)
