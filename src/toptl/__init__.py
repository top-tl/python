"""TOP.TL Python SDK.

Quickstart:
    from toptl import TopTL

    client = TopTL("toptl_xxx")
    client.post_stats("mybot", member_count=5_000, group_count=1_200)

    if client.has_voted("mybot", "123456789").voted:
        ...  # grant reward
"""

from .async_client import AsyncTopTL
from .autoposter import Autoposter, AsyncAutoposter
from .client import TopTL
from .exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    TopTLError,
    ValidationError,
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

__all__ = [
    "TopTL",
    "AsyncTopTL",
    "Autoposter",
    "AsyncAutoposter",
    "Listing",
    "VoteCheck",
    "Voter",
    "StatsResult",
    "WebhookConfig",
    "WebhookTestResult",
    "GlobalStats",
    "TopTLError",
    "AuthenticationError",
    "NotFoundError",
    "RateLimitError",
    "ValidationError",
]

__version__ = "0.1.1"
