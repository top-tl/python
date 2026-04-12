"""
toptl — Official Python SDK for TOP.TL
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
from .types import (
    GlobalStats,
    HasVotedResponse,
    Listing,
    PostStatsBody,
    PostStatsResponse,
    Vote,
    VotesResponse,
)

__all__ = [
    "TopTL",
    "AsyncTopTL",
    "AutoPoster",
    "TopTLError",
    "GlobalStats",
    "HasVotedResponse",
    "Listing",
    "PostStatsBody",
    "PostStatsResponse",
    "Vote",
    "VotesResponse",
]

__version__ = "1.0.0"
