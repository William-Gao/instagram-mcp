from __future__ import annotations

from typing import Any

from ..server import format_error, get_client, mcp

COMMENT_FIELDS = "id,text,timestamp,username,like_count,user{id,username},replies{id,text,timestamp,username,like_count}"


@mcp.tool()
async def get_comments(media_id: str, limit: int = 50) -> dict[str, Any]:
    """List comments on a media post.

    Args:
        media_id: Instagram media ID.
        limit: Number of comments to return (1-100, default 50).
    """
    try:
        client = get_client()
        data = await client.get(
            f"{media_id}/comments",
            params={"fields": COMMENT_FIELDS, "limit": max(1, min(100, limit))},
        )
        return {"ok": True, **data}
    except Exception as e:
        return format_error(e)


@mcp.tool()
async def post_comment(media_id: str, message: str) -> dict[str, Any]:
    """Post a top-level comment on one of your media posts.

    Args:
        media_id: Instagram media ID (must be your own post).
        message: Comment text (max 2200 characters).
    """
    try:
        client = get_client()
        data = await client.post(f"{media_id}/comments", params={"message": message})
        return {"ok": True, "comment": data}
    except Exception as e:
        return format_error(e)


@mcp.tool()
async def reply_to_comment(comment_id: str, message: str) -> dict[str, Any]:
    """Reply to a specific comment.

    Args:
        comment_id: ID of the comment to reply to.
        message: Reply text (max 2200 characters).
    """
    try:
        client = get_client()
        data = await client.post(f"{comment_id}/replies", params={"message": message})
        return {"ok": True, "reply": data}
    except Exception as e:
        return format_error(e)


@mcp.tool()
async def delete_comment(comment_id: str) -> dict[str, Any]:
    """Delete a comment on one of your media posts."""
    try:
        client = get_client()
        data = await client.delete(comment_id)
        return {"ok": True, **data}
    except Exception as e:
        return format_error(e)


@mcp.tool()
async def hide_comment(comment_id: str, hide: bool = True) -> dict[str, Any]:
    """Hide or unhide a comment.

    Args:
        comment_id: Comment ID.
        hide: True to hide, False to unhide.
    """
    try:
        client = get_client()
        data = await client.post(
            comment_id,
            params={"hide": "true" if hide else "false"},
        )
        return {"ok": True, **data}
    except Exception as e:
        return format_error(e)


@mcp.tool()
async def toggle_media_comments(media_id: str, enabled: bool) -> dict[str, Any]:
    """Enable or disable comments on a media post.

    Args:
        media_id: Instagram media ID (must be your own post).
        enabled: True to allow comments, False to disable.
    """
    try:
        client = get_client()
        data = await client.post(
            media_id,
            params={"comment_enabled": "true" if enabled else "false"},
        )
        return {"ok": True, **data}
    except Exception as e:
        return format_error(e)
