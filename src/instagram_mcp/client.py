from __future__ import annotations

import asyncio
from typing import Any

import httpx

from .config import Config


class InstagramAPIError(Exception):
    def __init__(self, message: str, code: int | None = None, subcode: int | None = None,
                 type_: str | None = None, fbtrace_id: str | None = None,
                 status_code: int | None = None):
        super().__init__(message)
        self.code = code
        self.subcode = subcode
        self.type = type_
        self.fbtrace_id = fbtrace_id
        self.status_code = status_code

    def to_dict(self) -> dict[str, Any]:
        return {
            "message": str(self),
            "code": self.code,
            "subcode": self.subcode,
            "type": self.type,
            "fbtrace_id": self.fbtrace_id,
            "status_code": self.status_code,
        }


class InstagramClient:
    """Thin async wrapper around graph.instagram.com.

    Only Instagram Platform API endpoints (Instagram Login flow). Does NOT use
    graph.facebook.com - those endpoints require a Facebook Page link.
    """

    def __init__(self, config: Config, http: httpx.AsyncClient | None = None) -> None:
        self.config = config
        self._http = http or httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0))
        self._owns_http = http is None

    async def __aenter__(self) -> InstagramClient:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    def _url(self, path: str) -> str:
        path = path.lstrip("/")
        # OAuth endpoints sit outside the versioned namespace
        if path.startswith(("access_token", "refresh_access_token", "oauth/")):
            return f"https://graph.instagram.com/{path}"
        return f"{self.config.base_url}/{path}"

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        retries: int = 2,
    ) -> dict[str, Any]:
        params = dict(params or {})
        params.setdefault("access_token", self.config.access_token)
        url = self._url(path)
        last_exc: Exception | None = None
        for attempt in range(retries + 1):
            try:
                response = await self._http.request(
                    method, url, params=params, data=data, files=files
                )
            except httpx.HTTPError as e:
                last_exc = e
                if attempt < retries:
                    await asyncio.sleep(0.5 * (2**attempt))
                    continue
                raise InstagramAPIError(f"HTTP error: {e}") from e

            try:
                payload = response.json()
            except ValueError:
                payload = {"raw": response.text}

            if response.is_success:
                return payload

            err = payload.get("error") if isinstance(payload, dict) else None
            if isinstance(err, dict):
                exc = InstagramAPIError(
                    err.get("message") or response.text,
                    code=err.get("code"),
                    subcode=err.get("error_subcode"),
                    type_=err.get("type"),
                    fbtrace_id=err.get("fbtrace_id"),
                    status_code=response.status_code,
                )
            else:
                exc = InstagramAPIError(
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    status_code=response.status_code,
                )

            # Retry on 5xx or rate limit
            if response.status_code in (429, 500, 502, 503, 504) and attempt < retries:
                await asyncio.sleep(1.5 * (2**attempt))
                continue
            raise exc

        if last_exc:
            raise InstagramAPIError(f"Request failed: {last_exc}") from last_exc
        raise InstagramAPIError("Request failed for unknown reason")

    async def get(self, path: str, **kwargs: Any) -> dict[str, Any]:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> dict[str, Any]:
        return await self.request("POST", path, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> dict[str, Any]:
        return await self.request("DELETE", path, **kwargs)
