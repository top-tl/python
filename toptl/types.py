"""Type definitions for TOP.TL API responses."""

from typing import Any, Dict, List, Optional

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict


class Listing(TypedDict, total=False):
    """A TOP.TL listing."""

    username: str
    title: str
    description: str
    category: str
    type: str
    member_count: int
    votes: int
    url: str
    avatar: str
    verified: bool
    featured: bool
    tags: List[str]


class Vote(TypedDict, total=False):
    """A vote on a listing."""

    user_id: int
    username: str
    timestamp: str


class VotesResponse(TypedDict, total=False):
    """Response from the votes endpoint."""

    votes: List[Vote]
    total: int


class HasVotedResponse(TypedDict):
    """Response from the has-voted endpoint."""

    voted: bool


class PostStatsBody(TypedDict, total=False):
    """Body for posting stats."""

    memberCount: int
    groupCount: int


class PostStatsResponse(TypedDict, total=False):
    """Response from posting stats."""

    success: bool


class GlobalStats(TypedDict, total=False):
    """Global TOP.TL statistics."""

    total_listings: int
    total_votes: int
    total_users: int
