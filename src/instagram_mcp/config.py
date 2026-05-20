from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    access_token: str
    app_id: str | None
    app_secret: str | None
    api_version: str
    base_url: str

    @classmethod
    def from_env(cls) -> Config:
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
        return cls(
            access_token=token,
            app_id=(os.getenv("INSTAGRAM_APP_ID") or None),
            app_secret=(os.getenv("INSTAGRAM_APP_SECRET") or None),
            api_version=version,
            base_url=f"https://graph.instagram.com/{version}",
        )
