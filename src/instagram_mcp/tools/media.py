from __future__ import annotations

from typing import Any

from ..server import format_error, get_client, mcp

MEDIA_FIELDS = (
    "id,caption,media_type,media_product_type,media_url,thumbnail_url,"
    "permalink,timestamp,username,like_count,comments_count,is_shared_to_feed,"
    "shortcode"
)

MEDIA_INSIGHT_METRICS = {
    "IMAGE": "reach,likes,comments,saved,shares,total_interactions,views",
    "VIDEO": "reach,likes,comments,saved,shares,total_interactions,views",
    "CAROUSEL_ALBUM": "reach,likes,comments,saved,shares,total_interactions,views",
    "REELS": "reach,likes,comments,saved,shares,total_interactions,views,ig_reels_avg_watch_time,ig_reels_video_view_total_time,reels_skip_rate",
    "STORY": "reach,replies,views,navigation",
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
async def get_media_insights(
    media_id: str,
    metrics: str | None = None,
    breakdown: str | None = None,
) -> dict[str, Any]:
    """Get performance insights (reach, likes, saves, etc.) for a media item.

    Args:
        media_id: Instagram media ID.
        metrics: Comma-separated metric list. Defaults are auto-selected per media type
            (IMAGE, VIDEO, CAROUSEL_ALBUM, REELS, STORY). Pass your own to override.
        breakdown: Optional breakdown dimension. Meta heavily restricts which breakdowns
            are valid at the media level. The ONLY two valid media-level breakdowns are:
            - "action_type" — works with the `profile_activity` metric (Feed posts and
              Stories only; not Reels).
            - "story_navigation_action_type" — works with the `navigation` metric on
              Stories only.
            Notably, `follow_type` (FOLLOWER vs NON_FOLLOWER) is NOT valid at the media
            level — Meta returns "Incompatible breakdowns" if you try. To get a
            follower/non-follower split, call `get_account_insights` with
            metric="views,reach" and breakdown="follow_type", or use the
            `get_account_audience_split` convenience tool. Similarly, demographic
            breakdowns (age/gender/country/city) are account-level only.
    """
    try:
        client = get_client()
        chosen = metrics
        if not chosen:
            info = await client.get(media_id, params={"fields": "media_type,media_product_type"})
            mtype = (info.get("media_product_type") or info.get("media_type") or "IMAGE").upper()
            chosen = MEDIA_INSIGHT_METRICS.get(mtype, MEDIA_INSIGHT_METRICS["IMAGE"])
        params: dict[str, Any] = {"metric": chosen}
        if breakdown:
            params["breakdown"] = breakdown
        data = await client.get(f"{media_id}/insights", params=params)
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
