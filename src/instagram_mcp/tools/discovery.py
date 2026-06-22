from __future__ import annotations

from typing import Any

from ..server import fb_required_error, format_error, get_config, get_fb_client, mcp


@mcp.tool()
async def business_discovery(
    target_username: str,
    include_media: bool = True,
    media_limit: int = 10,
) -> dict[str, Any]:
    """Look up a public Business or Creator account's profile.

    Requires Facebook Graph API access (set INSTAGRAM_FB_ACCESS_TOKEN and
    INSTAGRAM_FB_IG_USER_ID). The target account must itself be a public Business
    or Creator account (personal accounts are not visible via this endpoint).

    Args:
        target_username: Instagram username to inspect (without leading "@").
        include_media: Whether to include the target's recent media.
        media_limit: Number of recent media items to include (1-50, default 10).
    """
    fb = get_fb_client()
    if fb is None:
        return fb_required_error("business_discovery")
    config = get_config()
    if not config.fb_ig_user_id:
        return {
            "ok": False,
            "error": {
                "message": (
                    "INSTAGRAM_FB_IG_USER_ID is not set. Call discover_fb_setup "
                    "to find your IG Business Account ID, then add it to your env."
                ),
                "type": "FBIGUserIDMissing",
            },
        }
    username = target_username.lstrip("@")
    fields = "id,username,name,biography,followers_count,follows_count,media_count,profile_picture_url"
    if include_media:
        media_fields = (
            "id,media_type,media_product_type,media_url,thumbnail_url,permalink,"
            "caption,timestamp,like_count,comments_count"
        )
        limit = max(1, min(50, media_limit))
        fields += f",media.limit({limit}){{{media_fields}}}"
    discovery_query = f"business_discovery.username({username}){{{fields}}}"
    try:
        data = await fb.get(
            config.fb_ig_user_id,
            params={"fields": discovery_query},
        )
        return {"ok": True, **data}
    except Exception as e:
        return format_error(e)


@mcp.tool()
async def find_outlier_posts(
    target_username: str,
    ratio: float = 2.0,
    media_limit: int = 50,
    metric: str = "views",
) -> dict[str, Any]:
    """Find a creator's posts where engagement exceeds N x their follower count.

    Default: posts with views >= 2 x followers. Useful for finding "viral" content
    relative to a creator's normal audience, regardless of their follower scale.

    Args:
        target_username: Instagram username (without leading "@").
        ratio: Engagement-to-follower multiplier threshold (default 2.0).
        media_limit: How many recent posts to scan (default 50, max 50 per Meta limit).
        metric: Which engagement metric to compare. Options:
            "views" (default, uses view_count for Reels/videos; falls back to like_count for static),
            "likes" (use like_count for all media types),
            "comments" (use comments_count).
    """
    fb = get_fb_client()
    if fb is None:
        return fb_required_error("find_outlier_posts")
    config = get_config()
    if not config.fb_ig_user_id:
        return {
            "ok": False,
            "error": {
                "message": (
                    "INSTAGRAM_FB_IG_USER_ID is not set. Call discover_fb_setup first."
                ),
                "type": "FBIGUserIDMissing",
            },
        }
    username = target_username.lstrip("@")
    media_fields = (
        "id,media_type,media_product_type,permalink,caption,timestamp,"
        "like_count,comments_count,view_count,thumbnail_url,media_url"
    )
    limit = max(1, min(50, media_limit))
    fields = (
        f"followers_count,media_count,username,name,"
        f"media.limit({limit}){{{media_fields}}}"
    )
    discovery_query = f"business_discovery.username({username}){{{fields}}}"
    try:
        data = await fb.get(config.fb_ig_user_id, params={"fields": discovery_query})
    except Exception as e:
        return format_error(e)

    bd = data.get("business_discovery") or {}
    if not bd:
        return {
            "ok": False,
            "error": {
                "message": f"Could not resolve username {username} via business_discovery. "
                "The target may be a personal account, private, or not exist.",
                "type": "TargetNotFound",
            },
        }

    followers = bd.get("followers_count") or 0
    threshold = followers * ratio
    posts = (bd.get("media") or {}).get("data") or []

    def engagement(p: dict[str, Any]) -> int:
        if metric == "likes":
            return p.get("like_count") or 0
        if metric == "comments":
            return p.get("comments_count") or 0
        # Default "views": business_discovery DOES expose view_count for the target's
        # videos/reels (verified live). Static images have no plays, so fall back to
        # like_count for those.
        return p.get("view_count") or p.get("like_count") or 0

    enriched = []
    for p in posts:
        eng = engagement(p)
        enriched.append(
            {
                **p,
                "_engagement": eng,
                "_ratio_vs_followers": (eng / followers) if followers else None,
                "_above_threshold": eng >= threshold,
            }
        )
    outliers = [p for p in enriched if p.get("_above_threshold")]
    outliers.sort(key=lambda x: x.get("_engagement") or 0, reverse=True)

    return {
        "ok": True,
        "username": bd.get("username"),
        "name": bd.get("name"),
        "followers_count": followers,
        "media_count": bd.get("media_count"),
        "ratio_threshold": ratio,
        "metric": metric,
        "threshold_value": threshold,
        "scanned_posts": len(posts),
        "outlier_count": len(outliers),
        "outliers": outliers,
        "_note": (
            "The 'views' metric uses the target's real view_count (business_discovery "
            "exposes view_count for videos/reels); static images without a view_count "
            "fall back to like_count. Coverage is the most recent media.limit() posts "
            "(max 50 per Meta), not the account's full history."
        ),
    }


@mcp.tool()
async def analyze_competitor(target_username: str, media_limit: int = 50) -> dict[str, Any]:
    """One-call competitor breakdown: profile, recent post stats, top performers, engagement rate.

    Args:
        target_username: Instagram username (without leading "@").
        media_limit: How many recent posts to analyze (1-50).
    """
    fb = get_fb_client()
    if fb is None:
        return fb_required_error("analyze_competitor")
    config = get_config()
    if not config.fb_ig_user_id:
        return {
            "ok": False,
            "error": {"message": "INSTAGRAM_FB_IG_USER_ID is not set.", "type": "FBIGUserIDMissing"},
        }
    username = target_username.lstrip("@")
    media_fields = (
        "id,media_type,media_product_type,permalink,caption,timestamp,"
        "like_count,comments_count,view_count,thumbnail_url"
    )
    limit = max(1, min(50, media_limit))
    fields = (
        f"id,username,name,biography,followers_count,follows_count,media_count,"
        f"profile_picture_url,website,"
        f"media.limit({limit}){{{media_fields}}}"
    )
    try:
        data = await fb.get(
            config.fb_ig_user_id,
            params={"fields": f"business_discovery.username({username}){{{fields}}}"},
        )
    except Exception as e:
        return format_error(e)

    bd = data.get("business_discovery") or {}
    if not bd:
        return {
            "ok": False,
            "error": {
                "message": f"Could not resolve {username}",
                "type": "TargetNotFound",
            },
        }

    posts = (bd.get("media") or {}).get("data") or []
    followers = bd.get("followers_count") or 0

    def eng_rate(p: dict[str, Any]) -> float:
        if not followers:
            return 0.0
        likes = p.get("like_count") or 0
        comments = p.get("comments_count") or 0
        return (likes + comments) / followers

    by_type: dict[str, list[dict[str, Any]]] = {}
    for p in posts:
        t = (p.get("media_product_type") or p.get("media_type") or "UNKNOWN").upper()
        by_type.setdefault(t, []).append(p)

    type_stats = {}
    for t, ps in by_type.items():
        if not ps:
            continue
        rates = [eng_rate(p) for p in ps]
        likes = [p.get("like_count") or 0 for p in ps]
        views = [p.get("view_count") or 0 for p in ps]
        type_stats[t] = {
            "count": len(ps),
            "avg_likes": sum(likes) / len(likes),
            "median_likes": sorted(likes)[len(likes) // 2],
            "avg_views": sum(views) / len(views),
            "max_views": max(views),
            "avg_engagement_rate": sum(rates) / len(rates),
            "max_likes": max(likes),
        }

    top_5 = sorted(posts, key=lambda p: p.get("like_count") or 0, reverse=True)[:5]

    return {
        "ok": True,
        "profile": {
            "username": bd.get("username"),
            "name": bd.get("name"),
            "biography": bd.get("biography"),
            "website": bd.get("website"),
            "followers_count": followers,
            "follows_count": bd.get("follows_count"),
            "media_count": bd.get("media_count"),
            "follower_ratio": (followers / bd["follows_count"]) if bd.get("follows_count") else None,
        },
        "analyzed_posts": len(posts),
        "by_media_type": type_stats,
        "top_5_by_likes": [
            {
                "permalink": p.get("permalink"),
                "type": p.get("media_product_type") or p.get("media_type"),
                "like_count": p.get("like_count"),
                "comments_count": p.get("comments_count"),
                "view_count": p.get("view_count"),
                "engagement_rate": round(eng_rate(p), 4),
                "engagement_vs_followers_x": round(
                    (p.get("like_count") or 0) / followers, 2
                )
                if followers
                else None,
                "timestamp": p.get("timestamp"),
                "caption": (p.get("caption") or "")[:200],
            }
            for p in top_5
        ],
    }


@mcp.tool()
async def discover_fb_setup() -> dict[str, Any]:
    """Auto-discover your IG Business Account ID from a Facebook Page token.

    Call this once after generating a Facebook Page access token (EAA…) and adding it
    as INSTAGRAM_FB_ACCESS_TOKEN. This tool lists your FB Pages and their linked IG
    Business accounts. Copy the IG account ID into INSTAGRAM_FB_IG_USER_ID and restart
    the MCP server.
    """
    fb = get_fb_client()
    if fb is None:
        return fb_required_error("discover_fb_setup")
    try:
        # List the pages this user can manage
        pages = await fb.get("me/accounts", params={"fields": "id,name,instagram_business_account{id,username,name}"})
    except Exception as e:
        return format_error(e)

    linked = []
    unlinked = []
    for p in pages.get("data", []):
        ig = p.get("instagram_business_account")
        if ig:
            linked.append(
                {
                    "fb_page_id": p.get("id"),
                    "fb_page_name": p.get("name"),
                    "ig_business_account_id": ig.get("id"),
                    "ig_username": ig.get("username"),
                    "ig_name": ig.get("name"),
                }
            )
        else:
            unlinked.append({"fb_page_id": p.get("id"), "fb_page_name": p.get("name")})
    instructions = (
        "Set INSTAGRAM_FB_IG_USER_ID to the ig_business_account_id of the account "
        "you want to query from, then restart the MCP server."
    )
    return {
        "ok": True,
        "linked_pages": linked,
        "unlinked_pages": unlinked,
        "next_step": instructions,
    }
