from __future__ import annotations

from typing import Any

from ..server import format_error, get_client, mcp

MEDIA_FIELDS = (
    "id,caption,media_type,media_product_type,media_url,thumbnail_url,"
    "permalink,timestamp,username,like_count,comments_count,is_shared_to_feed,"
    "shortcode"
)

MEDIA_INSIGHT_METRICS = {
    "IMAGE": "impressions,reach,likes,comments,saved,shares,total_interactions,profile_visits,follows,profile_activity",
    "VIDEO": "impressions,reach,likes,comments,saved,shares,total_interactions,profile_visits,follows,video_views",
    "CAROUSEL_ALBUM": "impressions,reach,likes,comments,saved,shares,total_interactions",
    "REELS": "reach,likes,comments,saved,shares,total_interactions,plays,ig_reels_avg_watch_time,ig_reels_video_view_total_time",
    "STORY": "impressions,reach,replies,exits,taps_forward,taps_back",
}


@mcp.tool()
async def get_media_posts(limit: int = 25, after: str | None = None) -> dict[str, Any]:
    """List the authenticated account's recent media posts.

    Args:
        limit: Number of posts to return (1-100, default 25).
        after: Pagination cursor from a previous response (paging.cursors.after).
    """
    try:
        client = get_client()
        params: dict[str, Any] = {"fields": MEDIA_FIELDS, "limit": max(1, min(100, limit))}
        if after:
            params["after"] = after
        data = await client.get("me/media", params=params)
        return {"ok": True, **data}
    except Exception as e:
        return format_error(e)


@mcp.tool()
async def get_media_details(media_id: str) -> dict[str, Any]:
    """Get full details for a single media item by its Instagram media ID."""
    try:
        client = get_client()
        data = await client.get(media_id, params={"fields": MEDIA_FIELDS + ",children{id,media_type,media_url,thumbnail_url}"})
        return {"ok": True, "media": data}
    except Exception as e:
        return format_error(e)


@mcp.tool()
async def get_media_insights(media_id: str, metrics: str | None = None) -> dict[str, Any]:
    """Get performance insights (reach, likes, saves, etc.) for a media item.

    Args:
        media_id: Instagram media ID.
        metrics: Comma-separated metric list. Defaults are auto-selected per media type
            (IMAGE, VIDEO, CAROUSEL_ALBUM, REELS, STORY). Pass your own to override.
    """
    try:
        client = get_client()
        chosen = metrics
        if not chosen:
            info = await client.get(media_id, params={"fields": "media_type,media_product_type"})
            mtype = (info.get("media_product_type") or info.get("media_type") or "IMAGE").upper()
            chosen = MEDIA_INSIGHT_METRICS.get(mtype, MEDIA_INSIGHT_METRICS["IMAGE"])
        data = await client.get(f"{media_id}/insights", params={"metric": chosen})
        return {"ok": True, **data}
    except Exception as e:
        return format_error(e)


@mcp.tool()
async def get_stories() -> dict[str, Any]:
    """List currently active stories on the connected account. Stories expire after 24 hours."""
    try:
        client = get_client()
        data = await client.get(
            "me/stories",
            params={"fields": "id,media_type,media_url,thumbnail_url,permalink,timestamp"},
        )
        return {"ok": True, **data}
    except Exception as e:
        return format_error(e)


@mcp.tool()
async def get_mentions(limit: int = 25) -> dict[str, Any]:
    """List media where the connected account has been @mentioned or tagged.

    Args:
        limit: Number of items to return (1-50, default 25).
    """
    try:
        client = get_client()
        params: dict[str, Any] = {
            "fields": MEDIA_FIELDS,
            "limit": max(1, min(50, limit)),
        }
        data = await client.get("me/tags", params=params)
        return {"ok": True, **data}
    except Exception as e:
        return format_error(e)
