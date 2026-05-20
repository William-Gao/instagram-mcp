"""Verify the patched get_media_insights metric set works against live API."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(ROOT.parent / ".env")

from instagram_mcp.client import InstagramClient  # noqa: E402
from instagram_mcp.config import Config  # noqa: E402
from instagram_mcp.tools.media import MEDIA_INSIGHT_METRICS  # noqa: E402


async def main() -> None:
    config = Config.from_env()
    async with InstagramClient(config) as client:
        # Find a Reel
        posts = await client.get(
            "me/media",
            params={"fields": "id,media_type,media_product_type", "limit": 5},
        )
        for post in posts.get("data", []):
            mtype = post.get("media_product_type") or post.get("media_type", "")
            metric_key = mtype.upper()
            metrics = MEDIA_INSIGHT_METRICS.get(metric_key)
            if not metrics:
                continue
            print(f"\n=== {post['id']} ({metric_key}) ===")
            print(f"Metrics requested: {metrics}")
            try:
                result = await client.get(
                    f"{post['id']}/insights",
                    params={"metric": metrics},
                )
                names = [d.get("name") for d in result.get("data", [])]
                print(f"Got {len(names)} metrics: {names}")
            except Exception as e:
                print(f"FAILED: {e}")


if __name__ == "__main__":
    asyncio.run(main())
