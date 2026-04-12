"""Synchronous TOP.TL API client."""

import json
import urllib.request
import urllib.error
import urllib.parse
from typing import Any, Callable, Dict, List, Optional

from .types import (
    GlobalStats,
    HasVotedResponse,
    Listing,
    PostStatsResponse,
    VotesResponse,
)
from .autoposter import AutoPoster

BASE_URL = "https://top.tl/api/v1"


class TopTLError(Exception):
    """Base exception for TOP.TL API errors."""

    def __init__(self, message: str, status: int = 0, body: Any = None) -> None:
        super().__init__(message)
        self.status = status
        self.body = body


class TopTL:
    """Synchronous client for the TOP.TL API.

    Args:
        token: Your TOP.TL API token (``toptl_xxx``).
        base_url: Override the API base URL. Defaults to ``https://top.tl/api/v1``.
        timeout: Request timeout in seconds. Defaults to 15.

    Example::

        from toptl import TopTL

        client = TopTL("toptl_xxx")
        listing = client.get_listing("durov")
        print(listing["title"])
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
        self._autoposter: Optional[AutoPoster] = None

    # ── HTTP helpers ─────────────────────────────────────────────

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "User-Agent": "toptl-python/1.0.0",
        }

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        url = f"{self._base_url}{path}"
        if params:
            filtered = {k: v for k, v in params.items() if v is not None}
            if filtered:
                url += "?" + urllib.parse.urlencode(filtered)

        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, headers=self._headers(), method=method)

        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                resp_body = resp.read().decode("utf-8")
                if resp_body:
                    return json.loads(resp_body)
                return None
        except urllib.error.HTTPError as exc:
            resp_body = exc.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(resp_body)
            except (json.JSONDecodeError, ValueError):
                parsed = resp_body
            raise TopTLError(
                f"HTTP {exc.code}: {exc.reason}", status=exc.code, body=parsed
            ) from exc
        except urllib.error.URLError as exc:
            raise TopTLError(f"Request failed: {exc.reason}") from exc

    # ── API methods ──────────────────────────────────────────────

    def get_listing(self, username: str) -> Listing:
        """Get listing info by username.

        Args:
            username: The Telegram username (without ``@``).

        Returns:
            The listing data.
        """
        return self._request("GET", f"/v1/listing/{urllib.parse.quote(username, safe='')}")

    def get_votes(self, username: str, *, limit: int = 20) -> VotesResponse:
        """Get votes for a listing.

        Args:
            username: The Telegram username (without ``@``).
            limit: Maximum number of votes to return. Defaults to 20.

        Returns:
            Votes data including the list and total count.
        """
        return self._request(
            "GET",
            f"/v1/listing/{urllib.parse.quote(username, safe='')}/votes",
            params={"limit": limit},
        )

    def has_voted(self, username: str, telegram_id: int) -> HasVotedResponse:
        """Check if a Telegram user has voted for a listing.

        Args:
            username: The Telegram username (without ``@``).
            telegram_id: The Telegram user ID to check.

        Returns:
            Dict with a ``voted`` boolean.
        """
        return self._request(
            "GET",
            f"/v1/listing/{urllib.parse.quote(username, safe='')}/has-voted/{telegram_id}",
        )

    def post_stats(
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

        return self._request(
            "POST",
            f"/v1/listing/{urllib.parse.quote(username, safe='')}/stats",
            body=body,
        )

    def get_stats(self) -> GlobalStats:
        """Get global TOP.TL statistics.

        Returns:
            Global platform stats.
        """
        return self._request("GET", "/v1/stats")

    # ── Autoposter ───────────────────────────────────────────────

    def start_autopost(
        self,
        username: str,
        callback: Callable[[], Dict[str, Optional[int]]],
        *,
        interval: int = 1800,
    ) -> AutoPoster:
        """Start automatically posting stats in a background thread.

        Args:
            username: The listing username to post stats for.
            callback: A callable returning a dict with ``member_count``
                and/or ``group_count`` keys.
            interval: Seconds between posts. Defaults to 1800 (30 min).

        Returns:
            The :class:`AutoPoster` instance.
        """
        if self._autoposter is not None and self._autoposter.running:
            self._autoposter.stop()

        self._autoposter = AutoPoster(self, username, callback, interval)
        self._autoposter.start()
        return self._autoposter

    def stop_autopost(self) -> None:
        """Stop the running autoposter, if any."""
        if self._autoposter is not None:
            self._autoposter.stop()
            self._autoposter = None
