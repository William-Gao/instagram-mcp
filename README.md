# instagram-mcp

[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-1.2+-purple.svg)](https://modelcontextprotocol.io/)

A Model Context Protocol server for Instagram that uses Meta's **Instagram Platform API with Instagram Login** (`graph.instagram.com`, `IGAA…` tokens). **No Facebook Page required.** **No private/scraping APIs.** 27 tools covering profile, media, publishing, comments, insights, and DMs — verified live against a real account.

## How this is different from other Instagram MCPs

| Project | Auth model | FB Page required | Risk of ban | Tools | Status |
|---|---|---|---|---|---|
| **this (`William-Gao/instagram-mcp`)** | **Dual: IG Login + FB Graph** | **Optional** (only for discovery/hashtags) | **None — official API** | **30 (27 working ✅)** | Active |
| [`mcpware/instagram-mcp`](https://github.com/mcpware/instagram-mcp) | Facebook Graph API (`EAA…`) | Yes | None — official API | 23 | Active |
| [`AleemHaider/instagram-mcp`](https://github.com/AleemHaider/instagram-mcp) | Facebook Graph API (`EAA…`) | Yes | None — official API | ~15 | Active |
| [`supercorp-ai/instagram-mcp`](https://github.com/supercorp-ai/instagram-mcp) | Instagram Login API (`IGAA…`) | No | None — official API | 4 | Active |
| `instagrapi`-based MCPs (multiple) | Username/password / session cookies | No | **High** — private API, accounts banned | varies | Active |

The gap this fills: Meta launched **Instagram Login** in July 2024 so creators can use the API *without* a linked Facebook Page. Before this project, the only MCP that spoke that auth flow was `supercorp-ai/instagram-mcp` with 4 tools. Everything else either requires you to maintain a FB Page or scrapes Instagram through the unofficial mobile API.

**This server is the only one that supports BOTH auth paths simultaneously.** Configure just `INSTAGRAM_ACCESS_TOKEN` (IGAA) and you get the 24 core tools without a Facebook Page. Add `INSTAGRAM_FB_ACCESS_TOKEN` (EAA) on top and you unlock `business_discovery`, hashtag search, and the higher-level competitor-analysis tools — without giving up anything on the IG Login side.

**TL;DR — start with just IG Login. Add the FB Page later only if you need to look up other creators.**

## Tool catalog (27)

Status legend: ✅ working, ⚠ requires Advanced Access via Meta App Review, 🚫 not supported by the Instagram Login API (Facebook Graph API only).

### Auth & profile
- ✅ `validate_access_token` — verify the configured token
- ✅ `refresh_access_token` — extend a long-lived token by 60 days
- ✅ `get_profile_info` — bio, follower/following counts, media count, etc.
- ✅ `get_account_pages` — compatibility shim (Instagram Login has no Pages concept)

### Media
- ✅ `get_media_posts` — paginate the account's recent posts
- ✅ `get_media_details` — full details for a single media item (incl. carousel children)
- ✅ `get_media_insights` — reach/likes/saves/shares/views/etc. (auto-picks metrics by media type)
- ✅ `get_stories` — currently active stories (24h)
- ✅ `get_mentions` — posts tagging or @mentioning the account

### Publishing
- ✅ `publish_image` — single image post
- ✅ `publish_video` — single feed video
- ✅ `publish_reel` — Reels (vertical short video), incl. `share_to_feed` and **Trial Reels** (`trial=True`)
- ✅ `publish_carousel` — 2–10 image/video carousel
- ✅ `get_content_publishing_limit` — remaining posts in 24h window

All publish tools expose the full set of Instagram container parameters (see
[`POST /{ig-user-id}/media`](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media/)),
applied per media type:

| Parameter | image | video | reel | carousel | Notes |
|---|:---:|:---:|:---:|:---:|---|
| `caption` | ✅ | ✅ | ✅ | ✅ (parent) | max 2200 chars, 30 hashtags, 20 @mentions |
| `alt_text` | ✅ | – | – | ✅ (per item) | accessibility text, images only, max 1000 chars |
| `location_id` | ✅ | ✅ | ✅ | ✅ | Facebook Page ID of a location |
| `user_tags` | ✅ | ✅ | ✅ | ✅ (per item) | `[{"username","x","y"}]`; `x`/`y` (0–1) required for images |
| `product_tags` | ✅ | ✅ | – | ✅ (per item) | `[{"product_id","x","y"}]`, max 5; needs a Shopping catalog |
| `collaborators` | ✅ | – | ✅ | ✅ | up to 3 usernames; not allowed on trial reels |
| `is_ai_generated` | ✅ | ✅ | ✅ | ✅ | self-disclose AI-generated content |
| `is_paid_partnership` | ✅ | ✅ | ✅ | ✅ | mark as paid partnership |
| `share_to_feed` | – | – | ✅ | – | also show the reel in the Feed tab |
| `thumb_offset` | – | ✅ | ✅ | – | cover-frame timestamp (ms) |
| `cover_url` | – | – | ✅ | – | custom cover image (overrides `thumb_offset`) |
| `audio_name` | – | – | ✅ | – | rename the reel's original audio (one-time) |
| `trial` / `graduation_strategy` | – | – | ✅ | – | Trial Reel (non-followers first); `MANUAL` or `SS_PERFORMANCE` |

**Trial Reels:** pass `trial=True` to `publish_reel` to publish to non-followers
first. Requires ≥1,000 followers. `graduation_strategy="MANUAL"` keeps it
trial-only until you graduate it in the Instagram app; `"SS_PERFORMANCE"` lets
Meta auto-graduate it on early performance. (Resumable/`upload_type` chunked
uploads are not implemented — media is supplied by public URL only.)

**Examples** (tool arguments):

```python
# Image with alt text, a tagged user, and a location
publish_image(
    image_url="https://cdn.example.com/post.jpg",
    caption="Launch day 🚀 #startup",
    alt_text="Team holding a launch banner",
    user_tags=[{"username": "cofounder", "x": 0.5, "y": 0.4}],
    location_id="123456789",
)

# Trial Reel (shown to non-followers first), with a named original audio
publish_reel(
    video_url="https://cdn.example.com/clip.mp4",
    caption="3 money tips 👇",
    trial=True,
    graduation_strategy="MANUAL",
    audio_name="Quiet Wealth — Tip Drops",
)

# Carousel with per-item alt text / tags
publish_carousel(
    items=[
        {"image_url": "https://cdn.example.com/1.jpg", "alt_text": "Q1 chart"},
        {"video_url": "https://cdn.example.com/2.mp4"},
    ],
    caption="Swipe →",
    collaborators=["partnerhandle"],
)
```

### Comments
- ✅ `get_comments` — list comments + nested replies
- ✅ `post_comment` — top-level comment on your own post
- ✅ `reply_to_comment` — reply to a specific comment
- ✅ `delete_comment` — delete a comment
- ✅ `hide_comment` — hide/unhide a comment
- ✅ `toggle_media_comments` — enable/disable comments on a post

### Insights
- ✅ `get_account_insights` — reach, profile views, audience demographics, etc.

### Discovery (opt-in via FB Graph API — set `INSTAGRAM_FB_ACCESS_TOKEN`)
- ✅ `business_discovery` — public Business/Creator profile + recent media (incl. real `view_count` on their videos/reels)
- ✅ `search_hashtag` — resolve hashtag name to ID
- ✅ `get_hashtag_media` — top or recent media for a hashtag
- ✅ `find_outlier_posts` — posts where engagement is ≥ N × follower count (default 2×); the `views` metric uses the target's real `view_count`
- ✅ `analyze_competitor` — one-call breakdown: profile + per-media-type stats (likes + views) + top 5
- ✅ `discover_fb_setup` — auto-find your IG Business Account ID from a FB Page token

### Messaging (requires Advanced Access via Meta App Review)
- ⚠ `get_conversations` — list DM threads
- ⚠ `get_conversation_messages` — read messages in a thread
- ⚠ `send_dm` — send a DM (24-hour window rule applies)

## Prerequisites

1. **Python 3.10+**
2. **Instagram Professional account** (Business or Creator). Toggle this in the IG app: Settings → Account type and tools → Switch to Professional Account.
3. **Meta developer app** with **Instagram Platform → Instagram API with Instagram Login** added (not the Facebook flow). Configure these scopes:
   - `instagram_business_basic`
   - `instagram_business_content_publish`
   - `instagram_business_manage_comments`
   - `instagram_business_manage_messages` (optional, requires App Review)
4. **Long-lived access token** (starts with `IGAA…`). See [Meta's setup guide](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/get-started).

## Setup

```bash
git clone https://github.com/William-Gao/instagram-mcp.git
cd instagram-mcp
python -m venv .venv
source .venv/bin/activate
pip install -e .

cp .env.example .env
# edit .env and paste your IGAA access token
```

Smoke-test locally:

```bash
python -m instagram_mcp
# stdio MCP server; connect a client to verify
```

## Use with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "instagram": {
      "command": "/absolute/path/to/instagram-mcp/.venv/bin/python",
      "args": ["-m", "instagram_mcp"],
      "env": {
        "INSTAGRAM_ACCESS_TOKEN": "IGAA..."
      }
    }
  }
}
```

Restart Claude Desktop; the `instagram___*` tools will appear.

## Use with Claude Code / Cursor

```bash
claude mcp add instagram /absolute/path/to/instagram-mcp/.venv/bin/python -m instagram_mcp \
  --env INSTAGRAM_ACCESS_TOKEN=IGAA...
```

## Use with any other MCP client

This is a standard stdio MCP server. Point your client's MCP config at the `python -m instagram_mcp` command with `INSTAGRAM_ACCESS_TOKEN` set in the environment.

## Configuration

| Variable                       | Required | Description |
|--------------------------------|----------|-------------|
| `INSTAGRAM_ACCESS_TOKEN`       | Yes      | Long-lived token from the IG Login API (starts with `IGAA…`) |
| `INSTAGRAM_APP_ID`             | No       | Meta app ID. Used by `token_manager` for FB token debug/exchange. |
| `INSTAGRAM_APP_SECRET`         | No       | Meta app secret. Used by `token_manager` for FB token debug/exchange. |
| `INSTAGRAM_API_VERSION`        | No       | Graph API version (default `v23.0`) |
| `INSTAGRAM_FB_ACCESS_TOKEN`    | No       | Optional FB Graph API Page token (`EAA…`). Unlocks `business_discovery`, `find_outlier_posts`, `analyze_competitor`, hashtag search. |
| `INSTAGRAM_FB_IG_USER_ID`      | No       | Your IG Business Account ID (paired with the FB token above). Auto-discoverable via `discover_fb_setup`. |
| `INSTAGRAM_DATA_DIR`           | No       | Path for local persistence (default `~/.instagram-mcp/`). |

### Optional: enable Facebook Graph API extras

Meta deliberately restricts a handful of endpoints to the FB Graph API path (`graph.facebook.com`):

- `business_discovery` — look up any public Business/Creator account
- `ig_hashtag_search` / `top_media` / `recent_media` — hashtag analytics
- and the higher-level `find_outlier_posts` / `analyze_competitor` tools this server builds on top

You can opt in by giving the server a Facebook Page access token in addition to your `IGAA…` token. Steps:

1. **Link your IG account to a Facebook Page.** In IG: Settings → Accounts Center → Connected experiences → connect your FB Page. The Page can be brand-new and empty.
2. **Generate a Page access token** in the Meta dev console with these scopes: `pages_show_list`, `pages_read_engagement`, `instagram_basic`, `instagram_manage_insights`, `business_management`. You want the **long-lived** Page token (not user token).
3. **Set `INSTAGRAM_FB_ACCESS_TOKEN`** to that `EAA…` token.
4. **Call the `discover_fb_setup` tool** from your MCP client. It will list your Pages and their linked IG Business Account IDs.
5. **Set `INSTAGRAM_FB_IG_USER_ID`** to the IG Business Account ID returned in step 4.
6. **Restart your MCP client** (Claude Desktop quit + reopen, etc.).

Once configured, the previously-stubbed tools start hitting the FB Graph API and returning real data. Without these env vars set, those tools cleanly return a `FBGraphTokenMissing` error pointing back to this setup.

## Rate limits

- **Publishing:** 100 posts per rolling 24-hour window (check `get_content_publishing_limit`).
- **Hashtag search:** 30 unique hashtags per rolling 7-day window per account.
- **Graph calls:** Dynamic limit based on impressions; minimum 4800 calls per 24h.

## Token lifecycle

- **IGAA (Instagram Login) token** — long-lived tokens last **60 days** and can be refreshed any time after they're **≥24h old** (extends another 60 days).
- **FB Page token** (`EAA…`, for discovery) — effectively **non-expiring**, but Meta's **data-access window (~90 days)** eventually requires an interactive re-authorization.

### Managed refresh (recommended)

Use the **`refresh_tokens`** MCP tool, or run the module directly, to refresh the IGAA token *and persist it to `.env`*, plus report FB token health:

```bash
python -m instagram_mcp.token_manager          # refresh if due + report
python -m instagram_mcp.token_manager --force  # force an IGAA refresh attempt
```

Schedule that command (cron / Task Scheduler) every ~30 days so the IGAA token never lapses. It writes the new token, plus `INSTAGRAM_ACCESS_TOKEN_REFRESHED_AT` / `INSTAGRAM_ACCESS_TOKEN_EXPIRES_AT`, back to `.env` (the single source of truth — loaded by `config.py` regardless of cwd). Exit code **2** means a token is dead and needs attention.

> **It cannot self-heal a dead token.** A *fully expired/invalidated* IGAA token, or a lapsed FB data-access window, can only be fixed by an **interactive (browser) re-authorization** — Meta provides no programmatic path. In that case the report sets `needs_reauth: true`; treat it as an alert to re-run the login flow, not something automation can recover from.

## Contributing

PRs welcome. This started as a community-driven project to fill the gap where the existing Instagram MCP servers either require a Facebook Page or use risky private APIs.

```bash
pip install -e ".[dev]"
ruff check .
pytest
```

## License

MIT. See [LICENSE](LICENSE).

## Known limitations

The Instagram Login API is more restrictive than the Facebook Graph API in three areas:

1. **`business_discovery`** — Looking up arbitrary public profiles is not supported. The endpoint exists on `graph.facebook.com` only.
2. **Hashtag search** (`ig_hashtag_search`, `top_media`, `recent_media`) — Not exposed on `graph.instagram.com`. Only available via the FB Graph API path.
3. **DMs** — Available, but require `instagram_business_manage_messages` with Advanced Access. Meta only grants this after App Review.

If you need any of these three capabilities, you must link your IG to a Facebook Page and use a Facebook-Graph-based MCP like [`mcpware/instagram-mcp`](https://github.com/mcpware/instagram-mcp) or [`AleemHaider/instagram-mcp`](https://github.com/AleemHaider/instagram-mcp).

Two further limits apply to **all** Instagram APIs (official or otherwise), not just this one:

- **Close Friends targeting is not available.** The Content Publishing API exposes no audience/visibility parameter, and Meta's docs explicitly flag close-friends-only posts as unsupported. Everything published is public/to-followers; Close Friends is an Instagram-app-only feature.
- **Stories publishing is read-only here.** `get_stories` lists active stories, but there is no story-publish tool yet (the container flow supports `media_type=STORIES`; it's simply not wired up).

## Acknowledgements

- [supercorp-ai/instagram-mcp](https://github.com/supercorp-ai/instagram-mcp) — reference for the Instagram Login OAuth/refresh flow.
- Meta's [Instagram Platform documentation](https://developers.facebook.com/docs/instagram-platform/).
