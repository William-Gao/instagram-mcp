from __future__ import annotations

import asyncio
from typing import Any

from ..server import format_error, get_client, mcp

POLL_INTERVAL_SECS = 3
MAX_POLL_ATTEMPTS = 40  # ~2 minutes worst case for video processing


async def _wait_for_container(container_id: str) -> dict[str, Any]:
    client = get_client()
    last = {}
    for _ in range(MAX_POLL_ATTEMPTS):
        last = await client.get(container_id, params={"fields": "status_code,status"})
        status = last.get("status_code") or last.get("status")
        if status == "FINISHED":
            return last
        if status in {"ERROR", "EXPIRED"}:
            raise RuntimeError(f"Container {container_id} failed: {last}")
        await asyncio.sleep(POLL_INTERVAL_SECS)
    raise TimeoutError(f"Container {container_id} did not finish in time. Last status: {last}")


async def _publish_container(container_id: str) -> dict[str, Any]:
    client = get_client()
    return await client.post(
        "me/media_publish",
        params={"creation_id": container_id},
    )


@mcp.tool()
async def get_content_publishing_limit() -> dict[str, Any]:
    """Check how many posts you can still publish in the rolling 24h window."""
    try:
        client = get_client()
        data = await client.get(
            "me/content_publishing_limit",
            params={"fields": "quota_usage,config"},
        )
        return {"ok": True, **data}
    except Exception as e:
        return format_error(e)


@mcp.tool()
async def publish_image(image_url: str, caption: str | None = None) -> dict[str, Any]:
    """Publish a single image to Instagram.

    Args:
        image_url: Publicly accessible HTTPS URL to a JPEG/PNG image.
        caption: Optional caption (max 2200 chars, max 30 hashtags).
    """
    try:
        client = get_client()
        params: dict[str, Any] = {"image_url": image_url}
        if caption:
            params["caption"] = caption
        container = await client.post("me/media", params=params)
        cid = container.get("id")
        if not cid:
            return {"ok": False, "error": {"message": "No container id returned", "data": container}}
        await _wait_for_container(cid)
        published = await _publish_container(cid)
        return {"ok": True, "media_id": published.get("id"), "container_id": cid}
    except Exception as e:
        return format_error(e)


@mcp.tool()
async def publish_video(
    video_url: str,
    caption: str | None = None,
    thumb_offset: int | None = None,
) -> dict[str, Any]:
    """Publish a video to Instagram as a regular feed video.

    Args:
        video_url: Publicly accessible HTTPS URL to an MP4 video.
        caption: Optional caption.
        thumb_offset: Optional thumbnail timestamp in milliseconds.
    """
    try:
        client = get_client()
        params: dict[str, Any] = {"media_type": "VIDEO", "video_url": video_url}
        if caption:
            params["caption"] = caption
        if thumb_offset is not None:
            params["thumb_offset"] = thumb_offset
        container = await client.post("me/media", params=params)
        cid = container.get("id")
        if not cid:
            return {"ok": False, "error": {"message": "No container id returned", "data": container}}
        await _wait_for_container(cid)
        published = await _publish_container(cid)
        return {"ok": True, "media_id": published.get("id"), "container_id": cid}
    except Exception as e:
        return format_error(e)


@mcp.tool()
async def publish_reel(
    video_url: str,
    caption: str | None = None,
    share_to_feed: bool = True,
    thumb_offset: int | None = None,
    cover_url: str | None = None,
) -> dict[str, Any]:
    """Publish a Reel (short-form vertical video).

    Args:
        video_url: Publicly accessible HTTPS URL to an MP4 video.
        caption: Optional caption.
        share_to_feed: Whether to also share to the main feed (default True).
        thumb_offset: Optional thumbnail timestamp in milliseconds.
        cover_url: Optional custom cover image URL.
    """
    try:
        client = get_client()
        params: dict[str, Any] = {
            "media_type": "REELS",
            "video_url": video_url,
            "share_to_feed": "true" if share_to_feed else "false",
        }
        if caption:
            params["caption"] = caption
        if thumb_offset is not None:
            params["thumb_offset"] = thumb_offset
        if cover_url:
            params["cover_url"] = cover_url
        container = await client.post("me/media", params=params)
        cid = container.get("id")
        if not cid:
            return {"ok": False, "error": {"message": "No container id returned", "data": container}}
        await _wait_for_container(cid)
        published = await _publish_container(cid)
        return {"ok": True, "media_id": published.get("id"), "container_id": cid}
    except Exception as e:
        return format_error(e)


@mcp.tool()
async def publish_carousel(
    items: list[dict[str, Any]],
    caption: str | None = None,
) -> dict[str, Any]:
    """Publish a carousel (album) of 2-10 images or videos.

    Args:
        items: List of 2-10 items, each {"image_url": "..."} or {"video_url": "..."}.
        caption: Optional caption applied to the whole carousel.
    """
    try:
        if not (2 <= len(items) <= 10):
            return {"ok": False, "error": {"message": "Carousel requires 2-10 items"}}
        client = get_client()

        child_ids: list[str] = []
        for item in items:
            params: dict[str, Any] = {"is_carousel_item": "true"}
            if item.get("image_url"):
                params["image_url"] = item["image_url"]
            elif item.get("video_url"):
                params["media_type"] = "VIDEO"
                params["video_url"] = item["video_url"]
            else:
                return {"ok": False, "error": {"message": f"Item missing image_url or video_url: {item}"}}
            child = await client.post("me/media", params=params)
            cid = child.get("id")
            if not cid:
                return {"ok": False, "error": {"message": "No child container id returned", "data": child}}
            await _wait_for_container(cid)
            child_ids.append(cid)

        carousel_params: dict[str, Any] = {
            "media_type": "CAROUSEL",
            "children": ",".join(child_ids),
        }
        if caption:
            carousel_params["caption"] = caption
        parent = await client.post("me/media", params=carousel_params)
        pid = parent.get("id")
        if not pid:
            return {"ok": False, "error": {"message": "No carousel container id returned", "data": parent}}
        await _wait_for_container(pid)
        published = await _publish_container(pid)
        return {"ok": True, "media_id": published.get("id"), "container_id": pid, "child_ids": child_ids}
    except Exception as e:
        return format_error(e)
