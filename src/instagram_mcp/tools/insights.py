from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from ..server import format_error, get_client, mcp

DEFAULT_DAY_METRICS = "reach,profile_views,website_clicks,accounts_engaged"
DEFAULT_LIFETIME_METRICS = "follower_demographics,engaged_audience_demographics,reached_audience_demographics"


def _day_window(date: str | None) -> tuple[int, int]:
    if date:
        d = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        now = datetime.now(timezone.utc)
        d = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    start = int(d.timestamp())
    end = int((d + timedelta(days=1)).timestamp())
    return start, end


@mcp.tool()
async def get_account_insights(
    metrics: str | None = None,
    period: str = "day",
    metric_type: str = "total_value",
    since: int | None = None,
    until: int | None = None,
    breakdown: str | None = None,
) -> dict[str, Any]:
    """Get account-level insights.

    Args:
        metrics: Comma-separated metric list. Defaults vary by period.
        period: "day", "week", "days_28", or "lifetime".
        metric_type: "total_value" (default) or "time_series".
        since: Unix timestamp for start of range (optional).
        until: Unix timestamp for end of range (optional).
        breakdown: Optional breakdown (e.g. "age", "gender", "city", "country") for demographics.
    """
    try:
        client = get_client()
        chosen = metrics
        if not chosen:
            chosen = DEFAULT_LIFETIME_METRICS if period == "lifetime" else DEFAULT_DAY_METRICS
        params: dict[str, Any] = {
            "metric": chosen,
            "period": period,
            "metric_type": metric_type,
        }
        if since is not None:
            params["since"] = since
        if until is not None:
            params["until"] = until
        if breakdown:
            params["breakdown"] = breakdown
        data = await client.get("me/insights", params=params)
        return {"ok": True, **data}
    except Exception as e:
        return format_error(e)


@mcp.tool()
async def get_account_audience_split(
    date: str | None = None,
    metrics: str = "views,reach",
) -> dict[str, Any]:
    """Get account-level follower vs non-follower split, plus a media-type split, for a single day.

    Useful because per-Reel follower attribution is NOT available via the Instagram Graph
    API (Meta explicitly restricts media-level breakdowns). The closest signal is this
    account-level daily breakdown, which tells you:

      - How many views/reach came from FOLLOWER vs NON_FOLLOWER vs UNKNOWN for the day
      - How those views were distributed across REEL / STORY / POST / CAROUSEL

    Combined, you can infer the rough follower share of your Reels' audience on a given day,
    but you cannot attribute specific viewers to specific Reels.

    Args:
        date: Day to look up in YYYY-MM-DD (UTC). Defaults to today.
        metrics: Metrics to request. Default "views,reach". Both support follow_type and
            media_product_type breakdowns.
    """
    try:
        client = get_client()
        since, until = _day_window(date)
        common = {
            "metric": metrics,
            "period": "day",
            "metric_type": "total_value",
            "since": since,
            "until": until,
        }
        by_follow = await client.get("me/insights", params={**common, "breakdown": "follow_type"})
        by_type = await client.get(
            "me/insights", params={**common, "breakdown": "media_product_type"}
        )
        return {
            "ok": True,
            "date": (date or datetime.fromtimestamp(since, tz=timezone.utc).strftime("%Y-%m-%d")),
            "by_follow_type": by_follow.get("data", []),
            "by_media_product_type": by_type.get("data", []),
        }
    except Exception as e:
        return format_error(e)
