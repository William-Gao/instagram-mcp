from __future__ import annotations

from typing import Any

from ..server import fb_required_error, format_error, get_config, get_fb_client, mcp


@mcp.tool()
async def search_hashtag(hashtag: str) -> dict[str, Any]:
    """Look up a hashtag's Instagram ID.

    Requires Facebook Graph API access (INSTAGRAM_FB_ACCESS_TOKEN +
    INSTAGRAM_FB_IG_USER_ID). Returns the hashtag-id you'll pass to get_hashtag_media.

    Args:
        hashtag: Hashtag name with or without a leading "#" (max 100 chars).
    """
    fb = get_fb_client()
    if fb is None:
        return fb_required_error("search_hashtag")
    config = get_config()
    if not config.fb_ig_user_id:
        return {
            "ok": False,
            "error": {"message": "INSTAGRAM_FB_IG_USER_ID is not set.", "type": "FBIGUserIDMissing"},
        }
    name = hashtag.lstrip("#").strip()
    try:
        data = await fb.get(
            "ig_hashtag_search",
            params={"user_id": config.fb_ig_user_id, "q": name},
        )
        return {"ok": True, "hashtag": name, **data}
    except Exception as e:
        return format_error(e)


@mcp.tool()
async def get_hashtag_media(
    hashtag_id: str,
    media_type: str = "top",
    limit: int = 25,
) -> dict[str, Any]:
    """Get top or recent media for a hashtag.

    Requires Facebook Graph API access.

    Args:
        hashtag_id: Hashtag ID returned by search_hashtag.
        media_type: "top" (default) or "recent".
        limit: Number of posts to return (1-50).
    """
    fb = get_fb_client()
    if fb is None:
        return fb_required_error("get_hashtag_media")
    config = get_config()
    if not config.fb_ig_user_id:
        return {
            "ok": False,
            "error": {"message": "INSTAGRAM_FB_IG_USER_ID is not set.", "type": "FBIGUserIDMissing"},
        }
    edge = "top_media" if media_type == "top" else "recent_media"
    fields = "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count"
    try:
        data = await fb.get(
            f"{hashtag_id}/{edge}",
            params={
                "user_id": config.fb_ig_user_id,
                "fields": fields,
                "limit": max(1, min(50, limit)),
            },
        )
        return {"ok": True, **data}
    except Exception as e:
        return format_error(e)
