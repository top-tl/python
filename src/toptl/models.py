"""Typed response shapes for the TOP.TL public API.

Kept as lightweight dataclasses rather than Pydantic to avoid a heavy
dependency for SDK consumers. All `from_dict` constructors silently
ignore unknown fields so the SDK doesn't break when the API adds new
response keys.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Listing:
    id: str
    username: str
    title: str
    type: str  # 'CHANNEL' | 'GROUP' | 'BOT'
    description: str | None = None
    member_count: int = 0
    vote_count: int = 0
    languages: list[str] = field(default_factory=list)
    verified: bool = False
    featured: bool = False
    photo_url: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Listing:
        return cls(
            id=data.get("id", ""),
            username=data.get("username", ""),
            title=data.get("title", ""),
            type=data.get("type", ""),
            description=data.get("description"),
            member_count=int(data.get("memberCount") or 0),
            vote_count=int(data.get("voteCount") or 0),
            languages=list(data.get("languages") or []),
            verified=bool(data.get("verified")),
            featured=bool(data.get("featured")),
            photo_url=data.get("photoUrl"),
            raw=data,
        )


@dataclass
class Voter:
    user_id: str
    first_name: str | None = None
    username: str | None = None
    voted_at: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Voter:
        return cls(
            user_id=str(data.get("userId") or data.get("id") or ""),
            first_name=data.get("firstName"),
            username=data.get("username"),
            voted_at=data.get("votedAt") or data.get("createdAt"),
            raw=data,
        )


@dataclass
class VoteCheck:
    voted: bool
    voted_at: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VoteCheck:
        return cls(
            voted=bool(data.get("voted") or data.get("hasVoted")),
            voted_at=data.get("votedAt"),
            raw=data,
        )


@dataclass
class StatsResult:
    """Response from POST /v1/listing/{username}/stats."""

    success: bool
    username: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StatsResult:
        return cls(
            success=bool(data.get("success", True)),
            username=data.get("username"),
            raw=data,
        )


@dataclass
class WebhookConfig:
    url: str | None = None
    reward_title: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WebhookConfig:
        return cls(
            url=data.get("url") or data.get("webhookUrl"),
            reward_title=data.get("rewardTitle"),
            raw=data,
        )


@dataclass
class WebhookTestResult:
    success: bool
    status_code: int | None = None
    message: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WebhookTestResult:
        return cls(
            success=bool(data.get("success")),
            status_code=data.get("statusCode") or data.get("status"),
            message=data.get("message") or data.get("error"),
            raw=data,
        )


@dataclass
class GlobalStats:
    total: int = 0
    channels: int = 0
    groups: int = 0
    bots: int = 0
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GlobalStats:
        return cls(
            total=int(data.get("total") or 0),
            channels=int(data.get("channels") or 0),
            groups=int(data.get("groups") or 0),
            bots=int(data.get("bots") or 0),
            raw=data,
        )
