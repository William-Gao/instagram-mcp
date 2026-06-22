from __future__ import annotations

import asyncio
import json
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


def _add_common_params(
    params: dict[str, Any],
    *,
    caption: str | None = None,
    location_id: str | None = None,
    user_tags: list[dict[str, Any]] | None = None,
    product_tags: list[dict[str, Any]] | None = None,
    collaborators: list[str] | None = None,
    alt_text: str | None = None,
    is_ai_generated: bool = False,
    is_paid_partnership: bool = False,
) -> None:
    """Attach optional container parameters, JSON-encoding the array-valued ones.

    Callers pass only the subset of parameters the Instagram API supports for the
    media type they are creating (e.g. alt_text is image-only, collaborators are
    not allowed on plain videos or stories).
    """
    if caption:
        params["caption"] = caption
    if location_id:
        params["location_id"] = location_id
    if user_tags:
        params["user_tags"] = json.dumps(user_tags)
    if product_tags:
        params["product_tags"] = json.dumps(product_tags)
    if collaborators:
        params["collaborators"] = json.dumps(collaborators)
    if alt_text:
        params["alt_text"] = alt_text
    if is_ai_generated:
        params["is_ai_generated"] = "true"
    if is_paid_partnership:
        params["is_paid_partnership"] = "true"


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
async def publish_image(
    image_url: str,
    caption: str | None = None,
    alt_text: str | None = None,
    location_id: str | None = None,
    user_tags: list[dict[str, Any]] | None = None,
    product_tags: list[dict[str, Any]] | None = None,
    collaborators: list[str] | None = None,
    is_ai_generated: bool = False,
    is_paid_partnership: bool = False,
) -> dict[str, Any]:
    """Publish a single image to Instagram.

    Args:
        image_url: Publicly accessible HTTPS URL to a JPEG/PNG image.
        caption: Optional caption (max 2200 chars, max 30 hashtags, max 20 @mentions).
        alt_text: Accessibility text describing the image (max 1000 chars).
        location_id: Facebook Page ID of a location to tag.
        user_tags: People to tag, as [{"username": str, "x": float, "y": float}].
            x and y are 0.0-1.0 positions and are required for images.
        product_tags: Shopping tags, as [{"product_id": str, "x": float, "y": float}]
            (max 5). Requires an approved Instagram Shopping catalog.
        collaborators: Up to 3 Instagram usernames to invite as collaborators.
        is_ai_generated: Self-disclose that the content is AI-generated.
        is_paid_partnership: Mark the post as a paid partnership.
    """
    try:
        client = get_client()
        params: dict[str, Any] = {"image_url": image_url}
        _add_common_params(
            params,
            caption=caption,
            alt_text=alt_text,
            location_id=location_id,
            user_tags=user_tags,
            product_tags=product_tags,
            collaborators=collaborators,
            is_ai_generated=is_ai_generated,
            is_paid_partnership=is_paid_partnership,
        )
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
    location_id: str | None = None,
    user_tags: list[dict[str, Any]] | None = None,
    product_tags: list[dict[str, Any]] | None = None,
    is_ai_generated: bool = False,
    is_paid_partnership: bool = False,
) -> dict[str, Any]:
    """Publish a video to Instagram as a regular feed video.

    Args:
        video_url: Publicly accessible HTTPS URL to an MP4 video.
        caption: Optional caption.
        thumb_offset: Thumbnail timestamp in milliseconds.
        location_id: Facebook Page ID of a location to tag.
        user_tags: People to tag, as [{"username": str}] (coordinates ignored for video).
        product_tags: Shopping tags, as [{"product_id": str}] (max 5).
        is_ai_generated: Self-disclose that the content is AI-generated.
        is_paid_partnership: Mark the post as a paid partnership.
    """
    try:
        client = get_client()
        params: dict[str, Any] = {"media_type": "VIDEO", "video_url": video_url}
        if thumb_offset is not None:
            params["thumb_offset"] = thumb_offset
        _add_common_params(
            params,
            caption=caption,
            location_id=location_id,
            user_tags=user_tags,
            product_tags=product_tags,
            is_ai_generated=is_ai_generated,
            is_paid_partnership=is_paid_partnership,
        )
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
    audio_name: str | None = None,
    location_id: str | None = None,
    user_tags: list[dict[str, Any]] | None = None,
    collaborators: list[str] | None = None,
    is_ai_generated: bool = False,
    is_paid_partnership: bool = False,
    trial: bool = False,
    graduation_strategy: str = "MANUAL",
) -> dict[str, Any]:
    """Publish a Reel (short-form vertical video).

    Args:
        video_url: Publicly accessible HTTPS URL to an MP4 video.
        caption: Optional caption.
        share_to_feed: Whether to also share to the main feed (default True).
        thumb_offset: Thumbnail timestamp in milliseconds.
        cover_url: Custom cover image URL (takes precedence over thumb_offset).
        audio_name: Rename the reel's original audio track (can only be set once).
        location_id: Facebook Page ID of a location to tag.
        user_tags: People to tag, as [{"username": str}].
        collaborators: Up to 3 Instagram usernames to invite as collaborators.
            Ignored on trial reels (Instagram disallows collaborators on trials).
        is_ai_generated: Self-disclose that the content is AI-generated.
        is_paid_partnership: Mark the reel as a paid partnership.
        trial: If True, publish as a Trial Reel — shown only to non-followers
            initially. Requires the account to have at least 1,000 followers.
        graduation_strategy: How a trial reel graduates to all followers.
            "MANUAL" (default) keeps it trial-only until you graduate it in the
            Instagram app; "SS_PERFORMANCE" lets Meta auto-graduate it based on
            early performance with non-followers. Ignored unless trial=True.
    """
    try:
        client = get_client()
        params: dict[str, Any] = {
            "media_type": "REELS",
            "video_url": video_url,
            "share_to_feed": "true" if share_to_feed else "false",
        }
        if thumb_offset is not None:
            params["thumb_offset"] = thumb_offset
        if cover_url:
            params["cover_url"] = cover_url
        if audio_name:
            params["audio_name"] = audio_name
        if trial:
            if graduation_strategy not in {"MANUAL", "SS_PERFORMANCE"}:
                return {
                    "ok": False,
                    "error": {
                        "message": "graduation_strategy must be 'MANUAL' or 'SS_PERFORMANCE'"
                    },
                }
            params["trial_params"] = json.dumps({"graduation_strategy": graduation_strategy})
            collaborators = None  # not allowed on trial reels
        _add_common_params(
            params,
            caption=caption,
            location_id=location_id,
            user_tags=user_tags,
            collaborators=collaborators,
            is_ai_generated=is_ai_generated,
            is_paid_partnership=is_paid_partnership,
        )
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
    location_id: str | None = None,
    collaborators: list[str] | None = None,
    is_ai_generated: bool = False,
    is_paid_partnership: bool = False,
) -> dict[str, Any]:
    """Publish a carousel (album) of 2-10 images or videos.

    Args:
        items: List of 2-10 items. Each item is a dict with either "image_url" or
            "video_url", plus optional per-item "alt_text" (images only),
            "user_tags" ([{"username","x","y"}]) and "product_tags"
            ([{"product_id","x","y"}]).
        caption: Optional caption applied to the whole carousel.
        location_id: Facebook Page ID of a location to tag.
        collaborators: Up to 3 Instagram usernames to invite as collaborators.
        is_ai_generated: Self-disclose that the content is AI-generated.
        is_paid_partnership: Mark the post as a paid partnership.
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
            _add_common_params(
                params,
                alt_text=item.get("alt_text"),
                user_tags=item.get("user_tags"),
                product_tags=item.get("product_tags"),
            )
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
        _add_common_params(
            carousel_params,
            caption=caption,
            location_id=location_id,
            collaborators=collaborators,
            is_ai_generated=is_ai_generated,
            is_paid_partnership=is_paid_partnership,
        )
        parent = await client.post("me/media", params=carousel_params)
        pid = parent.get("id")
        if not pid:
            return {"ok": False, "error": {"message": "No carousel container id returned", "data": parent}}
        await _wait_for_container(pid)
        published = await _publish_container(pid)
        return {"ok": True, "media_id": published.get("id"), "container_id": pid, "child_ids": child_ids}
    except Exception as e:
        return format_error(e)
