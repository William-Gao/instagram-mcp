# instagram-mcp

[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-1.2+-purple.svg)](https://modelcontextprotocol.io/)

A Model Context Protocol server for Instagram that uses Meta's **Instagram Platform API with Instagram Login** (`graph.instagram.com`, `IGAA…` tokens). **No Facebook Page required.** **No private/scraping APIs.** 27 tools covering profile, media, publishing, comments, insights, and DMs — verified live against a real account.

## How this is different from other Instagram MCPs

| Project | Auth model | FB Page required | Risk of ban | Tools | Status |
|---|---|---|---|---|---|
| **this (`William-Gao/instagram-mcp`)** | **Instagram Login API** (`IGAA…`) | **No** | **None — official API** | **27 (24 working ✅)** | Active |
| [`mcpware/instagram-mcp`](https://github.com/mcpware/instagram-mcp) | Facebook Graph API (`EAA…`) | Yes | None — official API | 23 | Active |
| [`AleemHaider/instagram-mcp`](https://github.com/AleemHaider/instagram-mcp) | Facebook Graph API (`EAA…`) | Yes | None — official API | ~15 | Active |
| [`supercorp-ai/instagram-mcp`](https://github.com/supercorp-ai/instagram-mcp) | Instagram Login API (`IGAA…`) | No | None — official API | 4 | Active |
| `instagrapi`-based MCPs (multiple) | Username/password / session cookies | No | **High** — private API, accounts banned | varies | Active |

The gap this fills: Meta launched **Instagram Login** in July 2024 so creators can use the API *without* a linked Facebook Page. Before this project, the only MCP that spoke that auth flow was `supercorp-ai/instagram-mcp` with 4 tools. Everything else either requires you to maintain a FB Page or scrapes Instagram through the unofficial mobile API.

**TL;DR — if your access token starts with `IGAA…`, no other MCP gives you full coverage. That's why this exists.**

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
- ✅ `publish_reel` — Reels (vertical short video), with `share_to_feed`
- ✅ `publish_carousel` — 2–10 image/video carousel
- ✅ `get_content_publishing_limit` — remaining posts in 24h window

### Comments
- ✅ `get_comments` — list comments + nested replies
- ✅ `post_comment` — top-level comment on your own post
- ✅ `reply_to_comment` — reply to a specific comment
- ✅ `delete_comment` — delete a comment
- ✅ `hide_comment` — hide/unhide a comment
- ✅ `toggle_media_comments` — enable/disable comments on a post

### Insights
- ✅ `get_account_insights` — reach, profile views, audience demographics, etc.

### Discovery (FB Graph API only — these always return a friendly error)
- 🚫 `search_hashtag` — Instagram Login API does not expose `ig_hashtag_search`
- 🚫 `get_hashtag_media` — same restriction
- 🚫 `business_discovery` — Instagram Login API does not expose `business_discovery`

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

| Variable                  | Required | Description |
|---------------------------|----------|-------------|
| `INSTAGRAM_ACCESS_TOKEN`  | Yes      | Long-lived token from the IG Login API (starts with `IGAA…`) |
| `INSTAGRAM_APP_ID`        | No       | Meta app ID (currently unused; reserved for future OAuth helpers) |
| `INSTAGRAM_APP_SECRET`    | No       | Meta app secret (reserved for future OAuth helpers) |
| `INSTAGRAM_API_VERSION`   | No       | Graph API version (default `v23.0`) |

## Rate limits

- **Publishing:** 100 posts per rolling 24-hour window (check `get_content_publishing_limit`).
- **Hashtag search:** 30 unique hashtags per rolling 7-day window per account.
- **Graph calls:** Dynamic limit based on impressions; minimum 4800 calls per 24h.

## Token lifecycle

Long-lived tokens last **60 days**. Call `refresh_access_token` at least every 60 days (only works on tokens at least 24 hours old) and update `INSTAGRAM_ACCESS_TOKEN` in `.env` with the returned value.

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

## Acknowledgements

- [supercorp-ai/instagram-mcp](https://github.com/supercorp-ai/instagram-mcp) — reference for the Instagram Login OAuth/refresh flow.
- Meta's [Instagram Platform documentation](https://developers.facebook.com/docs/instagram-platform/).
