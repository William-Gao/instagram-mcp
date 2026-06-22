"""Combination / edge-case matrix for the tool branch logic.

Where test_tools.py is one happy path per tool, this exercises the actual
branches: param inclusion/omission, array JSON-encoding, trial vs collaborators,
limit clamping, mixed carousel items, and error/edge paths.
"""
from __future__ import annotations

import json

import httpx
import pytest
import respx

from instagram_mcp.tools import comments, discovery, hashtags, media, publish

IG = "https://graph.instagram.com/v23.0"
FB = "https://graph.facebook.com/v23.0"


def _resp(payload):
    return httpx.Response(200, json=payload)


def _setup_single_publish(container_id="C", media_id="M", status="FINISHED"):
    """Wire the standard container -> poll -> publish flow for a single-media post."""
    create = respx.post(f"{IG}/me/media").mock(return_value=_resp({"id": container_id}))
    respx.get(f"{IG}/{container_id}").mock(return_value=_resp({"status_code": status}))
    respx.post(f"{IG}/me/media_publish").mock(return_value=_resp({"id": media_id}))
    return create


# ---------- publish_image: optional param inclusion matrix ----------

@pytest.mark.parametrize(
    "kwargs, present, absent",
    [
        ({}, [], ["caption", "alt_text", "location_id", "user_tags", "product_tags",
                  "collaborators", "is_ai_generated", "is_paid_partnership"]),
        ({"caption": "c"}, ["caption"], ["alt_text", "user_tags"]),
        ({"alt_text": "a"}, ["alt_text"], ["caption"]),
        ({"location_id": "123"}, ["location_id"], ["caption"]),
        ({"is_ai_generated": True}, ["is_ai_generated"], ["is_paid_partnership"]),
        ({"is_ai_generated": False}, [], ["is_ai_generated"]),
        ({"is_paid_partnership": True}, ["is_paid_partnership"], ["is_ai_generated"]),
    ],
)
@respx.mock
async def test_publish_image_param_inclusion(env, kwargs, present, absent):
    create = _setup_single_publish()
    res = await publish.publish_image(image_url="https://x/i.jpg", **kwargs)
    assert res["ok"] is True
    q = create.calls.last.request.url.params
    for k in present:
        assert k in q, f"expected {k} present"
    for k in absent:
        assert k not in q, f"expected {k} absent"


@pytest.mark.parametrize(
    "param, value, expected",
    [
        ("user_tags", [{"username": "u", "x": 0.1, "y": 0.2}], [{"username": "u", "x": 0.1, "y": 0.2}]),
        ("product_tags", [{"product_id": "p1", "x": 0.3, "y": 0.4}], [{"product_id": "p1", "x": 0.3, "y": 0.4}]),
        ("collaborators", ["a", "b"], ["a", "b"]),
    ],
)
@respx.mock
async def test_publish_image_array_params_json_encoded(env, param, value, expected):
    create = _setup_single_publish()
    await publish.publish_image(image_url="https://x/i.jpg", **{param: value})
    assert json.loads(create.calls.last.request.url.params[param]) == expected


# ---------- publish_reel: trial / collaborators / share_to_feed ----------

@respx.mock
async def test_reel_trial_drops_collaborators(env):
    create = _setup_single_publish()
    await publish.publish_reel(video_url="https://x/v.mp4", trial=True, collaborators=["a", "b"])
    q = create.calls.last.request.url.params
    assert "trial_params" in q
    assert "collaborators" not in q  # collaborators not allowed on trial reels


@respx.mock
async def test_reel_collaborators_kept_when_not_trial(env):
    create = _setup_single_publish()
    await publish.publish_reel(video_url="https://x/v.mp4", trial=False, collaborators=["a"])
    q = create.calls.last.request.url.params
    assert json.loads(q["collaborators"]) == ["a"]
    assert "trial_params" not in q


@pytest.mark.parametrize("share, expected", [(True, "true"), (False, "false")])
@respx.mock
async def test_reel_share_to_feed(env, share, expected):
    create = _setup_single_publish()
    await publish.publish_reel(video_url="https://x/v.mp4", share_to_feed=share)
    assert create.calls.last.request.url.params["share_to_feed"] == expected


@pytest.mark.parametrize("strategy, ok", [("MANUAL", True), ("SS_PERFORMANCE", True), ("nope", False), ("", False)])
@respx.mock
async def test_reel_graduation_strategy_validation(env, strategy, ok):
    if ok:
        create = _setup_single_publish()
        res = await publish.publish_reel(video_url="https://x/v.mp4", trial=True, graduation_strategy=strategy)
        assert res["ok"] is True
        assert json.loads(create.calls.last.request.url.params["trial_params"])["graduation_strategy"] == strategy
    else:
        res = await publish.publish_reel(video_url="https://x/v.mp4", trial=True, graduation_strategy=strategy)
        assert res["ok"] is False


# ---------- publish_carousel: item count + mixed media + per-item fields ----------

@pytest.mark.parametrize("n, ok", [(1, False), (2, True), (10, True), (11, False)])
async def test_carousel_item_count_bounds(env, n, ok):
    items = [{"image_url": f"https://x/{i}.jpg"} for i in range(n)]
    if not ok:
        res = await publish.publish_carousel(items=items)
        assert res["ok"] is False
        return
    with respx.mock:
        respx.post(f"{IG}/me/media").mock(side_effect=[_resp({"id": f"c{i}"}) for i in range(n)] + [_resp({"id": "par"})])
        for i in range(n):
            respx.get(f"{IG}/c{i}").mock(return_value=_resp({"status_code": "FINISHED"}))
        respx.get(f"{IG}/par").mock(return_value=_resp({"status_code": "FINISHED"}))
        respx.post(f"{IG}/me/media_publish").mock(return_value=_resp({"id": "MC"}))
        res = await publish.publish_carousel(items=items)
        assert res["ok"] is True and len(res["child_ids"]) == n


@respx.mock
async def test_carousel_mixed_media_and_per_item_fields(env):
    posts = respx.post(f"{IG}/me/media").mock(side_effect=[
        _resp({"id": "c0"}), _resp({"id": "c1"}), _resp({"id": "par"}),
    ])
    for cid in ("c0", "c1", "par"):
        respx.get(f"{IG}/{cid}").mock(return_value=_resp({"status_code": "FINISHED"}))
    respx.post(f"{IG}/me/media_publish").mock(return_value=_resp({"id": "MC"}))
    res = await publish.publish_carousel(items=[
        {"image_url": "https://x/0.jpg", "alt_text": "first", "user_tags": [{"username": "u", "x": 0.1, "y": 0.1}]},
        {"video_url": "https://x/1.mp4"},
    ])
    assert res["ok"] is True
    child0 = posts.calls[0].request.url.params
    child1 = posts.calls[1].request.url.params
    assert child0["is_carousel_item"] == "true" and child0["alt_text"] == "first"
    assert json.loads(child0["user_tags"]) == [{"username": "u", "x": 0.1, "y": 0.1}]
    assert child1["media_type"] == "VIDEO" and child1["video_url"] == "https://x/1.mp4"


# ---------- error / status propagation ----------

@pytest.mark.parametrize("status", ["ERROR", "EXPIRED"])
@respx.mock
async def test_publish_container_failure_status(env, status):
    respx.post(f"{IG}/me/media").mock(return_value=_resp({"id": "C"}))
    respx.get(f"{IG}/C").mock(return_value=_resp({"status_code": status}))
    res = await publish.publish_image(image_url="https://x/i.jpg")
    assert res["ok"] is False


@respx.mock
async def test_publish_no_container_id(env):
    respx.post(f"{IG}/me/media").mock(return_value=_resp({}))  # no id
    res = await publish.publish_image(image_url="https://x/i.jpg")
    assert res["ok"] is False


@respx.mock
async def test_tool_surfaces_api_error_code(env):
    respx.get(f"{IG}/me/media").mock(
        return_value=httpx.Response(400, json={"error": {"message": "bad", "code": 100}})
    )
    res = await media.get_media_posts()
    assert res["ok"] is False
    assert res["error"]["code"] == 100


# ---------- limit / range clamping ----------

@pytest.mark.parametrize("req, clamped", [(0, "1"), (5, "5"), (100, "100"), (500, "100")])
@respx.mock
async def test_get_comments_limit_clamped(env, req, clamped):
    route = respx.get(f"{IG}/M1/comments").mock(return_value=_resp({"data": []}))
    await comments.get_comments("M1", limit=req)
    assert route.calls.last.request.url.params["limit"] == clamped


@pytest.mark.parametrize("req, clamped", [(0, "1"), (25, "25"), (50, "50"), (999, "50")])
@respx.mock
async def test_get_mentions_limit_clamped(env, req, clamped):
    route = respx.get(f"{IG}/me/tags").mock(return_value=_resp({"data": []}))
    await media.get_mentions(limit=req)
    assert route.calls.last.request.url.params["limit"] == clamped


@pytest.mark.parametrize("req, expected_limit", [(0, "media.limit(1)"), (10, "media.limit(10)"), (50, "media.limit(50)"), (200, "media.limit(50)")])
@respx.mock
async def test_business_discovery_media_limit_clamped(env, req, expected_limit):
    route = respx.get(f"{FB}/999").mock(return_value=_resp({"business_discovery": {}}))
    await discovery.business_discovery("acme", media_limit=req)
    assert expected_limit in route.calls.last.request.url.params["fields"]


@respx.mock
async def test_business_discovery_no_media_when_disabled(env):
    route = respx.get(f"{FB}/999").mock(return_value=_resp({"business_discovery": {}}))
    await discovery.business_discovery("acme", include_media=False)
    assert "media.limit" not in route.calls.last.request.url.params["fields"]


@pytest.mark.parametrize("mtype, edge", [("top", "top_media"), ("recent", "recent_media")])
@respx.mock
async def test_get_hashtag_media_edge_selection(env, mtype, edge):
    route = respx.get(f"{FB}/h1/{edge}").mock(return_value=_resp({"data": []}))
    res = await hashtags.get_hashtag_media("h1", media_type=mtype)
    assert res["ok"] is True and route.called
