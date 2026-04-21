"""Synchronous TOP.TL API client.

For async, use `toptl.AsyncTopTL` — same surface, asyncio-native.
"""

from __future__ import annotations

from typing import Any

import httpx

from ._shared import (
    DEFAULT_BASE_URL,
    DEFAULT_TIMEOUT,
    DEFAULT_USER_AGENT,
    build_stats_body,
    parse_json_or_text,
    raise_for_status,
)
from .models import (
    GlobalStats,
    Listing,
    StatsResult,
    VoteCheck,
    Voter,
    WebhookConfig,
    WebhookTestResult,
)


class TopTL:
    """Synchronous client for the TOP.TL public API.

    Parameters
    ----------
    api_key
        Your API key from https://top.tl/profile → API Keys.
    base_url
        Override only for self-hosted / staging environments.
    timeout
        Seconds before any HTTP request is abandoned. Default 15s.
    user_agent
        Custom UA suffix, e.g. `"mybot/1.0"`. Appended to the SDK's UA.
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        user_agent: str | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        ua = DEFAULT_USER_AGENT
        if user_agent:
            ua = f"{ua} {user_agent}"
        self._http = httpx.Client(
            base_url=self._base_url,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "User-Agent": ua,
                "Accept": "application/json",
            },
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> TopTL:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        resp = self._http.request(method, path, json=json, params=params)
        body = parse_json_or_text(resp.headers.get("content-type"), resp.text)
        raise_for_status(resp.status_code, body, str(resp.url))
        return body

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def get_listing(self, username: str) -> Listing:
        """Fetch a listing by its Telegram username (without leading `@`)."""
        data = self._request("GET", f"/v1/listing/{username}")
        return Listing.from_dict(data if isinstance(data, dict) else {})

    def get_votes(self, username: str, limit: int = 20) -> list[Voter]:
        """Recent voters for a listing (most recent first)."""
        data = self._request(
            "GET", f"/v1/listing/{username}/votes", params={"limit": limit}
        )
        items = data if isinstance(data, list) else data.get("items", [])
        return [Voter.from_dict(v) for v in items]

    def has_voted(self, username: str, user_id: str | int) -> VoteCheck:
        """Has this Telegram user id voted for the given listing?"""
        data = self._request(
            "GET", f"/v1/listing/{username}/has-voted/{user_id}"
        )
        return VoteCheck.from_dict(data if isinstance(data, dict) else {})

    def post_stats(
        self,
        username: str,
        *,
        member_count: int | None = None,
        group_count: int | None = None,
        channel_count: int | None = None,
        bot_serves: list[str] | None = None,
    ) -> StatsResult:
        """Update counters on a listing you own.

        Only the keyword arguments you pass are sent — the others are
        left untouched on the server. `bot_serves` is a list of
        group/channel usernames the bot operates in.
        """
        body = build_stats_body(member_count, group_count, channel_count, bot_serves)
        if not body:
            raise ValueError(
                "post_stats needs at least one of member_count, group_count, "
                "channel_count, or bot_serves"
            )
        data = self._request("POST", f"/v1/listing/{username}/stats", json=body)
        return StatsResult.from_dict(data if isinstance(data, dict) else {"success": True})

    def batch_post_stats(
        self, items: list[dict[str, Any]]
    ) -> list[StatsResult]:
        """Post stats for up to 25 listings in a single request.

        Each item must include a `username`, plus any of `member_count`,
        `group_count`, `channel_count`, `bot_serves`. Server returns a
        per-item result; items that failed are still present with
        `success=False` and an `error` in `raw`.
        """
        if not items:
            return []
        body: list[dict[str, Any]] = []
        for i in items:
            entry: dict[str, Any] = {"username": i["username"]}
            if "member_count" in i:
                entry["memberCount"] = i["member_count"]
            if "group_count" in i:
                entry["groupCount"] = i["group_count"]
            if "channel_count" in i:
                entry["channelCount"] = i["channel_count"]
            if "bot_serves" in i:
                entry["botServes"] = i["bot_serves"]
            body.append(entry)
        data = self._request("POST", "/v1/stats/batch", json=body)
        if not isinstance(data, list):
            return []
        return [StatsResult.from_dict(r) for r in data]

    def set_webhook(
        self,
        username: str,
        url: str,
        *,
        reward_title: str | None = None,
    ) -> WebhookConfig:
        """Register the URL TOP.TL should POST to when a user votes.

        The callback will receive a JSON body with user + vote metadata.
        Pass `reward_title` to show a badge in the voter's notification.
        """
        body: dict[str, Any] = {"url": url}
        if reward_title is not None:
            body["rewardTitle"] = reward_title
        data = self._request(
            "PUT", f"/v1/listing/{username}/webhook", json=body
        )
        return WebhookConfig.from_dict(data if isinstance(data, dict) else {"url": url})

    def test_webhook(self, username: str) -> WebhookTestResult:
        """Send a synthetic vote event to the listing's configured webhook."""
        data = self._request(
            "POST", f"/v1/listing/{username}/webhook/test"
        )
        return WebhookTestResult.from_dict(data if isinstance(data, dict) else {"success": False})

    def get_global_stats(self) -> GlobalStats:
        """Site-wide totals (channels / groups / bots / total listings)."""
        data = self._request("GET", "/v1/stats")
        return GlobalStats.from_dict(data if isinstance(data, dict) else {})
