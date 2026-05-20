from __future__ import annotations

from typing import Any

from ..server import format_error, get_client, mcp

DEFAULT_DAY_METRICS = "reach,profile_views,website_clicks,accounts_engaged"
DEFAULT_LIFETIME_METRICS = "follower_demographics,engaged_audience_demographics,reached_audience_demographics"


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
