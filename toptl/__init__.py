"""
toptl -- Official Python SDK for TOP.TL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Telegram directory at https://top.tl

Basic usage::

    from toptl import TopTL

    client = TopTL("toptl_xxx")
    listing = client.get_listing("durov")
    print(listing["title"])

Async usage::

    from toptl import AsyncTopTL

    async with AsyncTopTL("toptl_xxx") as client:
        listing = await client.get_listing("durov")

:copyright: (c) 2026 TOP.TL
:license: MIT
"""

from .client import TopTL, TopTLError
from .async_client import AsyncTopTL
from .autoposter import AutoPoster
from .integrations import aiogram_middleware, ptb_handler
from .types import (
    BatchStatsResponse,
    GlobalStats,
    HasVotedResponse,
    Listing,
    PostStatsBody,
    PostStatsResponse,
    Vote,
    VotesResponse,
    WebhookResponse,
    WebhookTestResponse,
)

__all__ = [
    "TopTL",
    "AsyncTopTL",
    "AutoPoster",
    "TopTLError",
    "aiogram_middleware",
    "ptb_handler",
    "BatchStatsResponse",
    "GlobalStats",
    "HasVotedResponse",
    "Listing",
    "PostStatsBody",
    "PostStatsResponse",
    "Vote",
    "VotesResponse",
    "WebhookResponse",
    "WebhookTestResponse",
]

__version__ = "1.1.0"
