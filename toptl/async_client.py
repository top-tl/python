"""Asynchronous TOP.TL API client (requires aiohttp)."""

import json
import urllib.parse
from typing import Any, Dict, List, Optional

from .types import (
    BatchStatsResponse,
    GlobalStats,
    HasVotedResponse,
    Listing,
    PostStatsResponse,
    VotesResponse,
    WebhookResponse,
    WebhookTestResponse,
)

BASE_URL = "https://top.tl/api/v1"


class AsyncTopTL:
    """Async client for the TOP.TL API.

    Requires ``aiohttp`` — install with ``pip install toptl[async]``.

    Args:
        token: Your TOP.TL API token (``toptl_xxx``).
        base_url: Override the API base URL. Defaults to ``https://top.tl/api/v1``.
        timeout: Request timeout in seconds. Defaults to 15.

    Example::

        import asyncio
        from toptl import AsyncTopTL

        async def main():
            client = AsyncTopTL("toptl_xxx")
            listing = await client.get_listing("durov")
            print(listing["title"])
            await client.close()

        asyncio.run(main())
    """

    def __init__(
        self,
        token: str,
        *,
        base_url: str = BASE_URL,
        timeout: int = 15,
    ) -> None:
        self._token = token
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session: Any = None  # aiohttp.ClientSession, lazily created

    async def _ensure_session(self) -> Any:
        if self._session is None or self._session.closed:
            try:
                import aiohttp
            except ImportError:
                raise ImportError(
                    "aiohttp is required for AsyncTopTL. "
                    "Install it with: pip install toptl[async]"
                )
            timeout = aiohttp.ClientTimeout(total=self._timeout)
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type": "application/json",
                    "User-Agent": "toptl-python/1.0.0",
                },
                timeout=timeout,
            )
        return self._session

    async def close(self) -> None:
        """Close the underlying HTTP session."""
        if self._session is not None and not self._session.closed:
            await self._session.close()
            self._session = None

    async def __aenter__(self) -> "AsyncTopTL":
        await self._ensure_session()
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()

    # ── HTTP helper ──────────────────────────────────────────────

    async def _request(
        self,
        method: str,
        path: str,
        *,
        body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        session = await self._ensure_session()
        url = f"{self._base_url}{path}"

        filtered_params: Optional[Dict[str, Any]] = None
        if params:
            filtered_params = {k: v for k, v in params.items() if v is not None}

        kwargs: Dict[str, Any] = {}
        if body is not None:
            kwargs["json"] = body
        if filtered_params:
            kwargs["params"] = filtered_params

        from .client import TopTLError

        async with session.request(method, url, **kwargs) as resp:
            resp_text = await resp.text()
            if resp.status >= 400:
                try:
                    parsed = json.loads(resp_text)
                except (json.JSONDecodeError, ValueError):
                    parsed = resp_text
                raise TopTLError(
                    f"HTTP {resp.status}: {resp.reason}",
                    status=resp.status,
                    body=parsed,
                )
            if resp_text:
                return json.loads(resp_text)
            return None

    # ── API methods ──────────────────────────────────────────────

    async def get_listing(self, username: str) -> Listing:
        """Get listing info by username.

        Args:
            username: The Telegram username (without ``@``).

        Returns:
            The listing data.
        """
        return await self._request(
            "GET", f"/v1/listing/{urllib.parse.quote(username, safe='')}"
        )

    async def get_votes(self, username: str, *, limit: int = 20) -> VotesResponse:
        """Get votes for a listing.

        Args:
            username: The Telegram username (without ``@``).
            limit: Maximum number of votes to return. Defaults to 20.

        Returns:
            Votes data including the list and total count.
        """
        return await self._request(
            "GET",
            f"/v1/listing/{urllib.parse.quote(username, safe='')}/votes",
            params={"limit": limit},
        )

    async def has_voted(self, username: str, telegram_id: int) -> HasVotedResponse:
        """Check if a Telegram user has voted for a listing.

        Args:
            username: The Telegram username (without ``@``).
            telegram_id: The Telegram user ID to check.

        Returns:
            Dict with a ``voted`` boolean.
        """
        return await self._request(
            "GET",
            f"/v1/listing/{urllib.parse.quote(username, safe='')}/has-voted/{telegram_id}",
        )

    async def post_stats(
        self,
        username: str,
        *,
        member_count: Optional[int] = None,
        group_count: Optional[int] = None,
    ) -> PostStatsResponse:
        """Post stats for a listing.

        Args:
            username: The Telegram username (without ``@``).
            member_count: The bot/channel member count.
            group_count: The number of groups the bot is in.

        Returns:
            Confirmation response.
        """
        body: Dict[str, Any] = {}
        if member_count is not None:
            body["memberCount"] = member_count
        if group_count is not None:
            body["groupCount"] = group_count

        return await self._request(
            "POST",
            f"/v1/listing/{urllib.parse.quote(username, safe='')}/stats",
            body=body,
        )

    async def get_stats(self) -> GlobalStats:
        """Get global TOP.TL statistics.

        Returns:
            Global platform stats.
        """
        return await self._request("GET", "/v1/stats")

    async def set_webhook(
        self,
        username: str,
        url: str,
        *,
        reward_title: Optional[str] = None,
    ) -> WebhookResponse:
        """Set up a webhook for vote notifications.

        Args:
            username: The Telegram username (without ``@``).
            url: The webhook URL to receive vote events.
            reward_title: Optional title shown to users after voting.

        Returns:
            Confirmation response.
        """
        body: Dict[str, Any] = {"url": url}
        if reward_title is not None:
            body["rewardTitle"] = reward_title

        return await self._request(
            "PUT",
            f"/v1/listing/{urllib.parse.quote(username, safe='')}/webhook",
            body=body,
        )

    async def test_webhook(self, username: str) -> WebhookTestResponse:
        """Send a test event to the configured webhook.

        Args:
            username: The Telegram username (without ``@``).

        Returns:
            Confirmation response.
        """
        return await self._request(
            "POST",
            f"/v1/listing/{urllib.parse.quote(username, safe='')}/webhook/test",
        )

    async def batch_post_stats(
        self, stats: List[Dict[str, Any]]
    ) -> BatchStatsResponse:
        """Post stats for multiple listings in one request.

        Args:
            stats: A list of dicts, each containing ``username`` and stat
                fields like ``memberCount``, ``groupCount``, etc.

        Returns:
            Batch confirmation response.
        """
        return await self._request("POST", "/v1/stats/batch", body=stats)
