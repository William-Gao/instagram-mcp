from __future__ import annotations

from typing import Any

from ..server import format_error, get_client, mcp


@mcp.tool()
async def get_conversations(limit: int = 20) -> dict[str, Any]:
    """List Instagram DM conversations.

    Requires the instagram_manage_messages permission with Advanced Access
    (granted via Meta App Review).

    Args:
        limit: Number of conversations to return (1-100, default 20).
    """
    try:
        client = get_client()
        data = await client.get(
            "me/conversations",
            params={
                "platform": "instagram",
                "fields": "id,updated_time,participants,messages.limit(1){message,from,created_time}",
                "limit": max(1, min(100, limit)),
            },
        )
        return {"ok": True, **data}
    except Exception as e:
        return format_error(e)


@mcp.tool()
async def get_conversation_messages(conversation_id: str, limit: int = 25) -> dict[str, Any]:
    """List messages in a specific Instagram DM conversation.

    Requires instagram_manage_messages with Advanced Access.

    Args:
        conversation_id: ID from get_conversations.
        limit: Number of messages to return (1-100, default 25).
    """
    try:
        client = get_client()
        data = await client.get(
            conversation_id,
            params={
                "fields": (
                    "messages.limit(" + str(max(1, min(100, limit))) +
                    "){id,created_time,from,to,message,attachments}"
                )
            },
        )
        return {"ok": True, **data}
    except Exception as e:
        return format_error(e)


@mcp.tool()
async def send_dm(recipient_id: str, message: str) -> dict[str, Any]:
    """Send an Instagram DM.

    Requires instagram_manage_messages with Advanced Access. Can only reply to
    users who have messaged you in the past 24 hours (24-hour window rule).

    Args:
        recipient_id: Instagram Scoped User ID (IGSID) of the recipient.
        message: Message text (max 1000 characters).
    """
    try:
        client = get_client()
        import json

        data = await client.post(
            "me/messages",
            data={
                "recipient": json.dumps({"id": recipient_id}),
                "message": json.dumps({"text": message}),
            },
        )
        return {"ok": True, **data}
    except Exception as e:
        return format_error(e)
