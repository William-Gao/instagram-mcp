from __future__ import annotations

from typing import Any

from ..server import format_error, get_client, mcp

PROFILE_FIELDS = (
    "id,username,name,account_type,media_count,followers_count,"
    "follows_count,biography,profile_picture_url,website"
)


@mcp.tool()
async def validate_access_token() -> dict[str, Any]:
    """Verify the configured Instagram access token by calling /me.

    Returns the authenticated account's id, username, and account_type on success,
    or a structured error on failure.
    """
    try:
        client = get_client()
        data = await client.get("me", params={"fields": "id,username,account_type"})
        return {"ok": True, "account": data}
    except Exception as e:
        return format_error(e)


@mcp.tool()
async def refresh_access_token() -> dict[str, Any]:
    """Refresh the current long-lived Instagram access token (extends by 60 days).

    Only works on long-lived tokens that are at least 24 hours old. The new token
    is returned but NOT persisted to .env; you must update your config manually.
    """
    try:
        client = get_client()
        data = await client.get(
            "refresh_access_token",
            params={"grant_type": "ig_refresh_token"},
        )
        return {"ok": True, "token": data, "note": "Update INSTAGRAM_ACCESS_TOKEN with the new access_token to persist."}
    except Exception as e:
        return format_error(e)


@mcp.tool()
async def get_profile_info() -> dict[str, Any]:
    """Get the connected Instagram account's full profile information.

    Returns id, username, display name, account_type, bio, follower/following
    counts, media count, profile picture URL, and website.
    """
    try:
        client = get_client()
        data = await client.get("me", params={"fields": PROFILE_FIELDS})
        return {"ok": True, "profile": data}
    except Exception as e:
        return format_error(e)


@mcp.tool()
async def get_account_pages() -> dict[str, Any]:
    """Compatibility shim: the Instagram Login API does not use Facebook Pages.

    Returns the connected Instagram account info instead. Included for parity
    with Facebook Graph API-based Instagram MCP servers.
    """
    try:
        client = get_client()
        data = await client.get("me", params={"fields": PROFILE_FIELDS})
        return {
            "ok": True,
            "note": (
                "Instagram Login API does not use Facebook Pages. "
                "Returning the connected IG account directly."
            ),
            "instagram_account": data,
        }
    except Exception as e:
        return format_error(e)
