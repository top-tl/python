"""Smoke tests — all hit a mocked httpx transport, no real network."""

from __future__ import annotations

import httpx
import pytest

from toptl import (
    AuthenticationError,
    GlobalStats,
    Listing,
    NotFoundError,
    RateLimitError,
    TopTL,
    ValidationError,
    VoteCheck,
)


def make_client(handler) -> TopTL:
    transport = httpx.MockTransport(handler)
    client = TopTL("toptl_test_key")
    # Replace the internal httpx client's transport without changing
    # base_url / headers.
    client._http = httpx.Client(
        base_url="https://top.tl/api",
        transport=transport,
        headers=client._http.headers,
    )
    return client


def test_get_listing_parses_shape():
    def handler(req: httpx.Request) -> httpx.Response:
        assert req.url.path == "/api/v1/listing/mybot"
        assert req.headers["authorization"] == "Bearer toptl_test_key"
        return httpx.Response(
            200,
            json={
                "id": "cm1",
                "username": "mybot",
                "title": "My Bot",
                "type": "BOT",
                "memberCount": 5000,
                "voteCount": 42,
                "languages": ["en", "ar"],
                "verified": True,
                "featured": False,
            },
        )

    client = make_client(handler)
    listing = client.get_listing("mybot")
    assert isinstance(listing, Listing)
    assert listing.username == "mybot"
    assert listing.member_count == 5000
    assert listing.languages == ["en", "ar"]
    assert listing.verified is True


def test_has_voted_true():
    def handler(req: httpx.Request) -> httpx.Response:
        assert req.url.path.endswith("/has-voted/123")
        return httpx.Response(200, json={"voted": True, "votedAt": "2026-04-22T10:00:00Z"})

    client = make_client(handler)
    check = client.has_voted("mybot", 123)
    assert isinstance(check, VoteCheck)
    assert check.voted is True
    assert check.voted_at == "2026-04-22T10:00:00Z"


def test_post_stats_strips_none_and_posts_camel_case():
    seen: dict = {}

    def handler(req: httpx.Request) -> httpx.Response:
        seen["body"] = req.content
        seen["method"] = req.method
        return httpx.Response(200, json={"success": True, "username": "mybot"})

    client = make_client(handler)
    client.post_stats("mybot", member_count=5000, group_count=None, channel_count=300)
    assert seen["method"] == "POST"
    assert b'"memberCount":5000' in seen["body"]
    assert b'"channelCount":300' in seen["body"]
    # group_count was None → must not appear in payload
    assert b"groupCount" not in seen["body"]


def test_post_stats_requires_some_field():
    client = make_client(lambda req: httpx.Response(200, json={}))
    with pytest.raises(ValueError):
        client.post_stats("mybot")


def test_401_raises_auth_error():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "Invalid API key"})

    client = make_client(handler)
    with pytest.raises(AuthenticationError):
        client.get_listing("mybot")


def test_404_raises_not_found():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Listing not found"})

    client = make_client(handler)
    with pytest.raises(NotFoundError):
        client.get_listing("ghost")


def test_429_raises_rate_limit():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"message": "Too many requests"})

    client = make_client(handler)
    with pytest.raises(RateLimitError):
        client.get_listing("mybot")


def test_400_raises_validation():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"message": "Bad payload"})

    client = make_client(handler)
    with pytest.raises(ValidationError):
        client.post_stats("mybot", member_count=-1)


def test_global_stats():
    def handler(req: httpx.Request) -> httpx.Response:
        assert req.url.path == "/api/v1/stats"
        return httpx.Response(
            200, json={"total": 100, "channels": 80, "groups": 15, "bots": 5}
        )

    client = make_client(handler)
    stats = client.get_global_stats()
    assert isinstance(stats, GlobalStats)
    assert stats.total == 100
    assert stats.channels == 80
