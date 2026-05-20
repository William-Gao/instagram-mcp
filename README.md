# instagram-mcp

[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-1.2+-purple.svg)](https://modelcontextprotocol.io/)

A feature-complete Model Context Protocol (MCP) server for the **Instagram Platform API with Instagram Login** (the modern flow Meta launched in July 2024). No Facebook Page required.

**Why this exists.** Every other Instagram MCP server falls into one of two camps:
1. Uses the old **Facebook Graph API** path (`graph.facebook.com`), which requires linking your IG account to a Facebook Page and using an `EAA…` token.
2. Uses the **unofficial private API** (instagrapi, username/password login, Chrome session scraping), which risks getting your account banned.

This server uses the **official Instagram Platform API with Instagram Login** (`graph.instagram.com`, `IGAA…` tokens) and exposes ~25 tools covering profile, media, publishing, comments, insights, hashtags, business discovery, and DMs.

## Tool catalog (25)

### Auth & profile
- `validate_access_token` — verify the configured token
- `refresh_access_token` — extend a long-lived token by 60 days
- `get_profile_info` — bio, follower/following counts, media count, etc.
- `get_account_pages` — compatibility shim (Instagram Login has no Pages concept)

### Media
- `get_media_posts` — paginate the account's recent posts
- `get_media_details` — full details for a single media item (incl. carousel children)
- `get_media_insights` — reach/likes/saves/shares/etc. (auto-picks metrics by media type)
- `get_stories` — currently active stories (24h)
- `get_mentions` — posts tagging or @mentioning the account

### Publishing
- `publish_image` — single image post
- `publish_video` — single feed video
- `publish_reel` — Reels (vertical short video), with `share_to_feed`
- `publish_carousel` — 2–10 image/video carousel
- `get_content_publishing_limit` — remaining posts in 24h window

### Comments
- `get_comments` — list comments + nested replies
- `post_comment` — top-level comment on your own post
- `reply_to_comment` — reply to a specific comment
- `delete_comment` — delete a comment
- `hide_comment` — hide/unhide a comment
- `toggle_media_comments` — enable/disable comments on a post

### Insights
- `get_account_insights` — reach, profile views, audience demographics, etc.

### Discovery
- `search_hashtag` — resolve hashtag name to ID
- `get_hashtag_media` — top or recent media for a hashtag
- `business_discovery` — public profile + recent media for any Business/Creator

### Messaging (requires Advanced Access)
- `get_conversations` — list DM threads
- `get_conversation_messages` — read messages in a thread
- `send_dm` — send a DM (24-hour window rule applies)

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
git clone https://github.com/williamgao/instagram-mcp.git
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

## Use with Droid

Add to `~/.factory/mcp.json`:

```json
{
  "mcpServers": {
    "instagram": {
      "command": "/absolute/path/to/instagram-mcp/.venv/bin/python",
      "args": ["-m", "instagram_mcp"],
      "env": {
        "INSTAGRAM_ACCESS_TOKEN": "IGAA..."
      },
      "disabled": false
    }
  }
}
```

Restart Droid; the `instagram___*` tools will appear.

## Use with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (same shape as Droid above). Restart Claude Desktop.

## Use with Claude Code / Cursor

```bash
claude mcp add instagram /absolute/path/to/instagram-mcp/.venv/bin/python -m instagram_mcp \
  --env INSTAGRAM_ACCESS_TOKEN=IGAA...
```

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

## Acknowledgements

- [supercorp-ai/instagram-mcp](https://github.com/supercorp-ai/instagram-mcp) — reference for the Instagram Login OAuth/refresh flow.
- Meta's [Instagram Platform documentation](https://developers.facebook.com/docs/instagram-platform/).
