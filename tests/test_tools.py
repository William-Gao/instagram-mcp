"""Tests for the Instagram tool functions — every tool, mocked via respx.

Network is fully mocked; these assert the request shape (URL/params/body) and the
returned envelope, not live data.
"""
from __future__ import annotations

import json

import httpx
import pytest
import respx

from instagram_mcp.tools import (
    auth,
    comments,
    discovery,
    hashtags,
    insights,
    media,
    messaging,
    publish,
)

IG = "https://graph.instagram.com/v23.0"
IG_ROOT = "https://graph.instagram.com"
FB = "https://graph.facebook.com/v23.0"


@pytest.fixture
def env(monkeypatch, tmp_path):
    """Hermetic env: no real .env, fresh server-global clients, test tokens."""
    import instagram_mcp.server as srv
    monkeypatch.setattr("instagram_mcp.config.ENV_PATH", tmp_path / ".env")
    monkeypatch.setattr("instagram_mcp.config.load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "IGTOK")
    monkeypatch.setenv("INSTAGRAM_FB_ACCESS_TOKEN", "EAATOK")
    monkeypatch.setenv("INSTAGRAM_FB_IG_USER_ID", "999")
    srv._client = srv._fb_client = srv._config = None
    yield
    srv._client = srv._fb_client = srv._config = None


def ok200(payload):
    return httpx.Response(200, json=payload)


# ---------------- auth ----------------

@respx.mock
async def test_validate_access_token(env):
    respx.get(f"{IG}/me").mock(return_value=ok200({"id": "1", "username": "me", "account_type": "MEDIA_CREATOR"}))
    res = await auth.validate_access_token()
    assert res["ok"] is True and res["account"]["username"] == "me"


@respx.mock
async def test_refresh_access_token(env):
    respx.get(f"{IG_ROOT}/refresh_access_token").mock(return_value=ok200({"access_token": "NEW", "expires_in": 5184000}))
    res = await auth.refresh_access_token()
    assert res["ok"] is True and res["token"]["access_token"] == "NEW"


@respx.mock
async def test_get_profile_info(env):
    respx.get(f"{IG}/me").mock(return_value=ok200({"id": "1", "username": "me", "followers_count": 10}))
    res = await auth.get_profile_info()
    assert res["ok"] is True and res["profile"]["followers_count"] == 10


@respx.mock
async def test_get_account_pages_shim(env):
    respx.get(f"{IG}/me").mock(return_value=ok200({"id": "1", "username": "me"}))
    res = await auth.get_account_pages()
    assert res["ok"] is True and "instagram_account" in res


# ---------------- comments ----------------

@respx.mock
async def test_get_comments(env):
    route = respx.get(f"{IG}/M1/comments").mock(return_value=ok200({"data": [{"id": "c1", "text": "hi"}]}))
    res = await comments.get_comments("M1", limit=10)
    assert res["ok"] is True and res["data"][0]["id"] == "c1"
    assert route.calls.last.request.url.params["limit"] == "10"


@respx.mock
async def test_post_comment(env):
    route = respx.post(f"{IG}/M1/comments").mock(return_value=ok200({"id": "c2"}))
    res = await comments.post_comment("M1", "nice")
    assert res["ok"] is True and res["comment"]["id"] == "c2"
    assert route.calls.last.request.url.params["message"] == "nice"


@respx.mock
async def test_reply_to_comment(env):
    route = respx.post(f"{IG}/c1/replies").mock(return_value=ok200({"id": "r1"}))
    res = await comments.reply_to_comment("c1", "thanks")
    assert res["ok"] is True and res["reply"]["id"] == "r1"
    assert route.calls.last.request.url.params["message"] == "thanks"


@respx.mock
async def test_delete_comment(env):
    respx.delete(f"{IG}/c1").mock(return_value=ok200({"success": True}))
    res = await comments.delete_comment("c1")
    assert res["ok"] is True


@respx.mock
async def test_hide_comment(env):
    route = respx.post(f"{IG}/c1").mock(return_value=ok200({"success": True}))
    res = await comments.hide_comment("c1", hide=True)
    assert res["ok"] is True
    assert route.calls.last.request.url.params["hide"] == "true"


@respx.mock
async def test_toggle_media_comments(env):
    route = respx.post(f"{IG}/M1").mock(return_value=ok200({"success": True}))
    res = await comments.toggle_media_comments("M1", enabled=False)
    assert res["ok"] is True
    assert route.calls.last.request.url.params["comment_enabled"] == "false"


# ---------------- discovery ----------------

@respx.mock
async def test_business_discovery_default_projection(env):
    route = respx.get(f"{FB}/999").mock(return_value=ok200({"business_discovery": {"followers_count": 100}}))
    res = await discovery.business_discovery("acme")
    assert res["ok"] is True
    fields = route.calls.last.request.url.params["fields"]
    assert fields.startswith("business_discovery.username(acme){")
    assert "media.limit(10)" in fields and "view_count" in fields


@respx.mock
async def test_business_discovery_custom_fields_passthrough(env):
    route = respx.get(f"{FB}/999").mock(return_value=ok200({"business_discovery": {"followers_count": 5}}))
    await discovery.business_discovery("acme", fields="followers_count,media.limit(3){id}")
    assert route.calls.last.request.url.params["fields"] == "business_discovery.username(acme){followers_count,media.limit(3){id}}"


async def test_business_discovery_requires_ig_user_id(env, monkeypatch):
    import instagram_mcp.server as srv
    monkeypatch.delenv("INSTAGRAM_FB_IG_USER_ID", raising=False)
    srv._client = srv._fb_client = srv._config = None
    res = await discovery.business_discovery("acme")
    assert res["ok"] is False and res["error"]["type"] == "FBIGUserIDMissing"


@respx.mock
async def test_discover_fb_setup(env):
    respx.get(f"{FB}/me/accounts").mock(return_value=ok200(
        {"data": [{"id": "p1", "name": "Page", "instagram_business_account": {"id": "ig1", "username": "u"}}]}
    ))
    res = await discovery.discover_fb_setup()
    assert res["ok"] is True and res["linked_pages"][0]["ig_business_account_id"] == "ig1"


# ---------------- hashtags ----------------

@respx.mock
async def test_search_hashtag(env):
    route = respx.get(f"{FB}/ig_hashtag_search").mock(return_value=ok200({"data": [{"id": "h1"}]}))
    res = await hashtags.search_hashtag("#startup")
    assert res["ok"] is True and res["data"][0]["id"] == "h1"
    assert route.calls.last.request.url.params["q"] == "startup"


@respx.mock
async def test_get_hashtag_media(env):
    respx.get(f"{FB}/h1/top_media").mock(return_value=ok200({"data": [{"id": "m1"}]}))
    res = await hashtags.get_hashtag_media("h1", media_type="top", limit=5)
    assert res["ok"] is True and res["data"][0]["id"] == "m1"


# ---------------- insights ----------------

@respx.mock
async def test_get_account_insights(env):
    route = respx.get(f"{IG}/me/insights").mock(return_value=ok200({"data": [{"name": "reach"}]}))
    res = await insights.get_account_insights()
    assert res["ok"] is True
    assert "metric" in route.calls.last.request.url.params


@respx.mock
async def test_get_account_audience_split(env):
    respx.get(f"{IG}/me/insights").mock(return_value=ok200({"data": [{"name": "views"}]}))
    res = await insights.get_account_audience_split(date="2026-06-20")
    assert res["ok"] is True
    assert "by_follow_type" in res and "by_media_product_type" in res


# ---------------- media ----------------

@respx.mock
async def test_get_media_posts(env):
    respx.get(f"{IG}/me/media").mock(return_value=ok200({"data": [{"id": "1"}, {"id": "2"}]}))
    res = await media.get_media_posts(limit=2)
    assert res["ok"] is True and len(res["data"]) == 2


@respx.mock
async def test_get_media_details(env):
    respx.get(f"{IG}/M1").mock(return_value=ok200({"id": "M1", "media_type": "IMAGE"}))
    res = await media.get_media_details("M1")
    assert res["ok"] is True and res["media"]["id"] == "M1"


@respx.mock
async def test_get_media_insights_auto_metrics(env):
    # first call resolves media type, second fetches insights
    respx.get(f"{IG}/M1").mock(return_value=ok200({"media_product_type": "REELS"}))
    respx.get(f"{IG}/M1/insights").mock(return_value=ok200({"data": [{"name": "reach"}]}))
    res = await media.get_media_insights("M1")
    assert res["ok"] is True


@respx.mock
async def test_get_stories(env):
    respx.get(f"{IG}/me/stories").mock(return_value=ok200({"data": []}))
    res = await media.get_stories()
    assert res["ok"] is True


@respx.mock
async def test_get_mentions(env):
    respx.get(f"{IG}/me/tags").mock(return_value=ok200({"data": [{"id": "t1"}]}))
    res = await media.get_mentions(limit=5)
    assert res["ok"] is True and res["data"][0]["id"] == "t1"


# ---------------- messaging ----------------

@respx.mock
async def test_get_conversations(env):
    respx.get(f"{IG}/me/conversations").mock(return_value=ok200({"data": [{"id": "conv1"}]}))
    res = await messaging.get_conversations(limit=5)
    assert res["ok"] is True and res["data"][0]["id"] == "conv1"


@respx.mock
async def test_get_conversation_messages(env):
    respx.get(f"{IG}/conv1").mock(return_value=ok200({"messages": {"data": [{"id": "msg1"}]}}))
    res = await messaging.get_conversation_messages("conv1", limit=5)
    assert res["ok"] is True


@respx.mock
async def test_send_dm(env):
    route = respx.post(f"{IG}/me/messages").mock(return_value=ok200({"message_id": "mid1"}))
    res = await messaging.send_dm("IGSID123", "hello")
    assert res["ok"] is True and res["message_id"] == "mid1"
    body = route.calls.last.request.content.decode()
    assert "IGSID123" in body and "hello" in body


# ---------------- publish ----------------

@respx.mock
async def test_get_content_publishing_limit(env):
    respx.get(f"{IG}/me/content_publishing_limit").mock(
        return_value=ok200({"data": [{"quota_usage": 0, "config": {"quota_total": 100}}]})
    )
    res = await publish.get_content_publishing_limit()
    assert res["ok"] is True and res["data"][0]["quota_usage"] == 0


@respx.mock
async def test_publish_image_flow_and_params(env):
    create = respx.post(f"{IG}/me/media").mock(return_value=ok200({"id": "CONT1"}))
    respx.get(f"{IG}/CONT1").mock(return_value=ok200({"status_code": "FINISHED"}))
    pub = respx.post(f"{IG}/me/media_publish").mock(return_value=ok200({"id": "MEDIA1"}))
    res = await publish.publish_image(
        image_url="https://x/i.jpg", caption="hi", alt_text="a cat",
        user_tags=[{"username": "u", "x": 0.5, "y": 0.5}],
    )
    assert res["ok"] is True and res["media_id"] == "MEDIA1"
    q = create.calls.last.request.url.params
    assert q["image_url"] == "https://x/i.jpg" and q["caption"] == "hi" and q["alt_text"] == "a cat"
    assert json.loads(q["user_tags"]) == [{"username": "u", "x": 0.5, "y": 0.5}]
    assert pub.calls.last.request.url.params["creation_id"] == "CONT1"


@respx.mock
async def test_publish_video(env):
    create = respx.post(f"{IG}/me/media").mock(return_value=ok200({"id": "CV"}))
    respx.get(f"{IG}/CV").mock(return_value=ok200({"status_code": "FINISHED"}))
    respx.post(f"{IG}/me/media_publish").mock(return_value=ok200({"id": "MV"}))
    res = await publish.publish_video(video_url="https://x/v.mp4", caption="c")
    assert res["ok"] is True and res["media_id"] == "MV"
    assert create.calls.last.request.url.params["media_type"] == "VIDEO"


@respx.mock
async def test_publish_reel_trial_params(env):
    create = respx.post(f"{IG}/me/media").mock(return_value=ok200({"id": "C2"}))
    respx.get(f"{IG}/C2").mock(return_value=ok200({"status_code": "FINISHED"}))
    respx.post(f"{IG}/me/media_publish").mock(return_value=ok200({"id": "M2"}))
    res = await publish.publish_reel(video_url="https://x/v.mp4", trial=True, graduation_strategy="SS_PERFORMANCE")
    assert res["ok"] is True
    assert json.loads(create.calls.last.request.url.params["trial_params"]) == {"graduation_strategy": "SS_PERFORMANCE"}


async def test_publish_reel_bad_graduation_strategy(env):
    res = await publish.publish_reel(video_url="https://x/v.mp4", trial=True, graduation_strategy="NOPE")
    assert res["ok"] is False and "graduation_strategy" in res["error"]["message"]


@respx.mock
async def test_publish_carousel(env):
    respx.post(f"{IG}/me/media").mock(side_effect=[
        ok200({"id": "ch1"}), ok200({"id": "ch2"}), ok200({"id": "par"}),
    ])
    respx.get(f"{IG}/ch1").mock(return_value=ok200({"status_code": "FINISHED"}))
    respx.get(f"{IG}/ch2").mock(return_value=ok200({"status_code": "FINISHED"}))
    respx.get(f"{IG}/par").mock(return_value=ok200({"status_code": "FINISHED"}))
    respx.post(f"{IG}/me/media_publish").mock(return_value=ok200({"id": "MC"}))
    res = await publish.publish_carousel(items=[
        {"image_url": "https://x/1.jpg"}, {"image_url": "https://x/2.jpg"},
    ], caption="album")
    assert res["ok"] is True and res["media_id"] == "MC"
    assert res["child_ids"] == ["ch1", "ch2"]


@respx.mock
async def test_publish_image_container_error_surfaces(env):
    respx.post(f"{IG}/me/media").mock(return_value=ok200({"id": "C3"}))
    respx.get(f"{IG}/C3").mock(return_value=ok200({"status_code": "ERROR"}))
    res = await publish.publish_image(image_url="https://x/i.jpg")
    assert res["ok"] is False
