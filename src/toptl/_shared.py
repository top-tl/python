"""Helpers shared by the sync and async clients.

Keeping request-shape + error-mapping logic in one place so the two
clients stay identical in everything except the transport.
"""

from __future__ import annotations

from typing import Any

from .exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    TopTLError,
    ValidationError,
)

DEFAULT_BASE_URL = "https://top.tl/api"
DEFAULT_USER_AGENT = "toptl-python/0.1.0"
DEFAULT_TIMEOUT = 15.0


def build_stats_body(
    member_count: int | None,
    group_count: int | None,
    channel_count: int | None,
    bot_serves: list[str] | None,
) -> dict[str, Any]:
    """Camel-case JSON body for POST /v1/listing/{username}/stats.

    The public API accepts any subset of these keys; we strip `None` so
    fields the caller didn't touch aren't overwritten on the server.
    """
    body: dict[str, Any] = {}
    if member_count is not None:
        body["memberCount"] = int(member_count)
    if group_count is not None:
        body["groupCount"] = int(group_count)
    if channel_count is not None:
        body["channelCount"] = int(channel_count)
    if bot_serves is not None:
        body["botServes"] = list(bot_serves)
    return body


def raise_for_status(status_code: int, body: Any, url: str) -> None:
    """Map HTTP error codes to SDK exceptions. No-op on 2xx."""
    if 200 <= status_code < 300:
        return

    # Server's error message, when present, is the most actionable text —
    # prefer it over the HTTP reason phrase.
    message: str
    if isinstance(body, dict):
        message = str(
            body.get("message")
            or body.get("error")
            or f"HTTP {status_code}"
        )
    else:
        message = f"HTTP {status_code}"

    message = f"{message} ({url})"

    if status_code in (401, 403):
        raise AuthenticationError(
            message, status_code=status_code, response_body=body
        )
    if status_code == 404:
        raise NotFoundError(
            message, status_code=status_code, response_body=body
        )
    if status_code == 429:
        raise RateLimitError(
            message, status_code=status_code, response_body=body
        )
    if 400 <= status_code < 500:
        raise ValidationError(
            message, status_code=status_code, response_body=body
        )
    raise TopTLError(
        message, status_code=status_code, response_body=body
    )


def parse_json_or_text(content_type: str | None, text: str) -> Any:
    """Return decoded JSON when the server said so, else the raw text.

    The API is JSON-only but error pages from upstream infra (e.g.
    Cloudflare 502) come back as HTML — returning the raw text keeps the
    error path informative.
    """
    import json

    if content_type and "application/json" in content_type:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
    return text
