"""TOP.TL SDK exception hierarchy."""

from __future__ import annotations

from typing import Any


class TopTLError(Exception):
    """Base for every exception this SDK raises."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_body: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class AuthenticationError(TopTLError):
    """401/403 — invalid or missing API key, or key missing the required scope."""


class NotFoundError(TopTLError):
    """404 — listing or resource does not exist."""


class RateLimitError(TopTLError):
    """429 — API rate limit hit. Retry after a backoff."""


class ValidationError(TopTLError):
    """400 — request payload was rejected by the server."""
