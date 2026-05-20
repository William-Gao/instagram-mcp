"""Read-only smoke test against the live Instagram Platform API.

Requires INSTAGRAM_ACCESS_TOKEN in the environment (or .env in CWD).
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

# Allow loading .env from the parent content-creation workspace too
from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")
if not os.getenv("INSTAGRAM_ACCESS_TOKEN"):
    load_dotenv(ROOT.parent / ".env")

from instagram_mcp.client import InstagramClient  # noqa: E402
from instagram_mcp.config import Config  # noqa: E402


async def main() -> None:
    config = Config.from_env()
    print(f"Using API base: {config.base_url}")
    async with InstagramClient(config) as client:
        print("\n[1] validate_access_token (GET /me)")
        me = await client.get("me", params={"fields": "id,username,account_type"})
        print(json.dumps(me, indent=2))

        print("\n[2] get_profile_info")
        profile = await client.get(
            "me",
            params={
                "fields": (
                    "id,username,name,account_type,media_count,followers_count,"
                    "follows_count,biography,profile_picture_url,website"
                )
            },
        )
        print(json.dumps(profile, indent=2))

        print("\n[3] get_media_posts (limit=3)")
        media = await client.get(
            "me/media",
            params={
                "fields": "id,caption,media_type,permalink,timestamp,like_count,comments_count",
                "limit": 3,
            },
        )
        print(json.dumps(media, indent=2)[:1500])

        print("\n[4] get_content_publishing_limit")
        limit = await client.get(
            "me/content_publishing_limit",
            params={"fields": "quota_usage,config"},
        )
        print(json.dumps(limit, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
