from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# The repo-root .env is the single source of truth for tokens/credentials.
# Resolve it relative to this file so it loads regardless of the process cwd
# (an MCP server is rarely launched from the repo directory).
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


@dataclass(frozen=True)
class Config:
    access_token: str
    app_id: str | None
    app_secret: str | None
    api_version: str
    base_url: str
    data_dir: str
    fb_access_token: str | None
    fb_ig_user_id: str | None
    fb_base_url: str

    @classmethod
    def from_env(cls) -> Config:
        # Load the repo .env first (authoritative), then fall back to a cwd .env.
        # Neither overrides variables already present in the process environment,
        # so an explicit env var still wins if you need to override.
        load_dotenv(ENV_PATH)
        load_dotenv()
        token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "").strip()
        if not token:
            raise RuntimeError(
                "INSTAGRAM_ACCESS_TOKEN is required. "
                "Generate one at https://developers.facebook.com/ using the "
                "Instagram API with Instagram Login flow."
            )
        version = os.getenv("INSTAGRAM_API_VERSION", "v23.0").strip()
        if not version.startswith("v"):
            version = f"v{version}"
        data_dir = os.getenv("INSTAGRAM_DATA_DIR", "").strip() or os.path.expanduser(
            "~/.instagram-mcp"
        )
        fb_token = (os.getenv("INSTAGRAM_FB_ACCESS_TOKEN") or "").strip() or None
        fb_ig_user_id = (os.getenv("INSTAGRAM_FB_IG_USER_ID") or "").strip() or None
        return cls(
            access_token=token,
            app_id=(os.getenv("INSTAGRAM_APP_ID") or None),
            app_secret=(os.getenv("INSTAGRAM_APP_SECRET") or None),
            api_version=version,
            base_url=f"https://graph.instagram.com/{version}",
            data_dir=data_dir,
            fb_access_token=fb_token,
            fb_ig_user_id=fb_ig_user_id,
            fb_base_url=f"https://graph.facebook.com/{version}",
        )

    @property
    def has_fb_graph(self) -> bool:
        return self.fb_access_token is not None
