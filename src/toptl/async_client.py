"""Asynchronous TOP.TL API client — mirrors `TopTL` one-to-one."""

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


class AsyncTopTL:
    """Async client for the TOP.TL public API."""

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
        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "User-Agent": ua,
                "Accept": "application/json",
            },
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> AsyncTopTL:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        resp = await self._http.request(method, path, json=json, params=params)
        body = parse_json_or_text(resp.headers.get("content-type"), resp.text)
        raise_for_status(resp.status_code, body, str(resp.url))
        return body

    async def get_listing(self, username: str) -> Listing:
        data = await self._request("GET", f"/v1/listing/{username}")
        return Listing.from_dict(data if isinstance(data, dict) else {})

    async def get_votes(self, username: str, limit: int = 20) -> list[Voter]:
        data = await self._request(
            "GET", f"/v1/listing/{username}/votes", params={"limit": limit}
        )
        items = data if isinstance(data, list) else data.get("items", [])
        return [Voter.from_dict(v) for v in items]

    async def has_voted(self, username: str, user_id: str | int) -> VoteCheck:
        data = await self._request(
            "GET", f"/v1/listing/{username}/has-voted/{user_id}"
        )
        return VoteCheck.from_dict(data if isinstance(data, dict) else {})

    async def post_stats(
        self,
        username: str,
        *,
        member_count: int | None = None,
        group_count: int | None = None,
        channel_count: int | None = None,
        bot_serves: list[str] | None = None,
    ) -> StatsResult:
        body = build_stats_body(member_count, group_count, channel_count, bot_serves)
        if not body:
            raise ValueError(
                "post_stats needs at least one of member_count, group_count, "
                "channel_count, or bot_serves"
            )
        data = await self._request(
            "POST", f"/v1/listing/{username}/stats", json=body
        )
        return StatsResult.from_dict(data if isinstance(data, dict) else {"success": True})

    async def batch_post_stats(
        self, items: list[dict[str, Any]]
    ) -> list[StatsResult]:
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
        data = await self._request("POST", "/v1/stats/batch", json=body)
        if not isinstance(data, list):
            return []
        return [StatsResult.from_dict(r) for r in data]

    async def set_webhook(
        self,
        username: str,
        url: str,
        *,
        reward_title: str | None = None,
    ) -> WebhookConfig:
        body: dict[str, Any] = {"url": url}
        if reward_title is not None:
            body["rewardTitle"] = reward_title
        data = await self._request(
            "PUT", f"/v1/listing/{username}/webhook", json=body
        )
        return WebhookConfig.from_dict(data if isinstance(data, dict) else {"url": url})

    async def test_webhook(self, username: str) -> WebhookTestResult:
        data = await self._request(
            "POST", f"/v1/listing/{username}/webhook/test"
        )
        return WebhookTestResult.from_dict(data if isinstance(data, dict) else {"success": False})

    async def get_global_stats(self) -> GlobalStats:
        data = await self._request("GET", "/v1/stats")
        return GlobalStats.from_dict(data if isinstance(data, dict) else {})
