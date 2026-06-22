from __future__ import annotations

from typing import Any

from ..server import fb_required_error, format_error, get_config, get_fb_client, mcp


@mcp.tool()
async def business_discovery(
    target_username: str,
    fields: str | None = None,
    include_media: bool = True,
    media_limit: int = 10,
) -> dict[str, Any]:
    """Raw Business Discovery API lookup of a public Business/Creator account.

    Thin pass-through to Meta's business_discovery edge:
      GET /{ig-user-id}?fields=business_discovery.username(<handle>){<projection>}

    Requires Facebook Graph API access (INSTAGRAM_FB_ACCESS_TOKEN and
    INSTAGRAM_FB_IG_USER_ID). The target must be a public Business or Creator
    account (personal/private accounts are not visible via this endpoint).

    Args:
        target_username: Instagram username to inspect (without leading "@").
        fields: Optional explicit business_discovery projection, passed through
            verbatim — e.g. "followers_count,media.limit(5){id,view_count,like_count}".
            When provided, `include_media`/`media_limit` are ignored and you control
            the whole field set. When omitted, a sensible default profile + recent
            media projection is used (media includes the public `view_count`).
        include_media: Include recent media in the default projection (ignored when
            `fields` is supplied).
        media_limit: Number of recent media items in the default projection (1-50).
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
    if fields:
        projection = fields
    else:
        projection = (
            "id,username,name,biography,website,followers_count,follows_count,"
            "media_count,profile_picture_url"
        )
        if include_media:
            media_fields = (
                "id,media_type,media_product_type,media_url,thumbnail_url,permalink,"
                "caption,timestamp,like_count,comments_count,view_count"
            )
            limit = max(1, min(50, media_limit))
            projection += f",media.limit({limit}){{{media_fields}}}"
    discovery_query = f"business_discovery.username({username}){{{projection}}}"
    try:
        data = await fb.get(config.fb_ig_user_id, params={"fields": discovery_query})
        return {"ok": True, **data}
    except Exception as e:
        return format_error(e)


@mcp.tool()
async def discover_fb_setup() -> dict[str, Any]:
    """Auto-discover your IG Business Account ID from a Facebook Page token.

    Call this once after generating a Facebook Page access token (EAA…) and adding it
    as INSTAGRAM_FB_ACCESS_TOKEN. This tool lists your FB Pages and their linked IG
    Business accounts. Copy the IG account ID into INSTAGRAM_FB_IG_USER_ID and restart
    the MCP server.

    Note: this needs a Facebook *user* token (the `/me/accounts` edge). A long-lived
    *Page* token has no `accounts` edge — if you've already switched to one, you don't
    need this tool anymore (you already have your IG Business Account ID).
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
