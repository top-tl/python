# toptl

[![PyPI version](https://img.shields.io/pypi/v/toptl.svg?label=pypi&color=3775a9)](https://pypi.org/project/toptl/)
[![Python versions](https://img.shields.io/pypi/pyversions/toptl.svg?color=3776ab)](https://pypi.org/project/toptl/)
[![Downloads](https://img.shields.io/pypi/dm/toptl.svg?color=blue)](https://pypi.org/project/toptl/)
[![License](https://img.shields.io/pypi/l/toptl.svg?color=green)](https://github.com/top-tl/python/blob/main/LICENSE)
[![Typed](https://img.shields.io/pypi/types/toptl.svg?color=blue)](https://pypi.org/project/toptl/)
[![TOP.TL](https://img.shields.io/badge/top.tl-developers-2ec4b6)](https://top.tl/developers)

The official Python SDK for **TOP.TL** — post stats, check votes, and manage vote webhooks for your Telegram bot, channel, or group listed on [top.tl](https://top.tl).

## Install

```bash
pip install toptl
```

Requires Python 3.9+. Depends on `httpx` for transport.

## Quickstart

Get an API key at https://top.tl/profile → **API Keys**. Scope the key to your listing and the operations you need (`listing:read`, `listing:write`, `votes:read`, `votes:check`).

```python
from toptl import TopTL

client = TopTL("toptl_xxx")

# Fetch a listing
listing = client.get_listing("mybot")
print(listing.title, listing.vote_count)

# Post stats on a listing you own
client.post_stats(
    "mybot",
    member_count=5_000,
    group_count=1_200,
    channel_count=300,
)

# Reward users who voted
check = client.has_voted("mybot", user_id=123456789)
if check.voted:
    grant_premium_access(user_id=123456789)
```

## Async

Same surface, `asyncio`-native:

```python
import asyncio
from toptl import AsyncTopTL

async def main():
    async with AsyncTopTL("toptl_xxx") as client:
        stats = await client.get_global_stats()
        print(stats.channels, stats.groups, stats.bots)

asyncio.run(main())
```

## Autoposter

For long-running bot processes, the SDK ships with a background autoposter that calls `post_stats` on an interval and only hits the API when the stats actually changed:

```python
from toptl import TopTL, Autoposter

client = TopTL("toptl_xxx")
poster = Autoposter(
    client,
    "mybot",
    callback=lambda: {"member_count": get_user_count()},
    interval_seconds=30 * 60,   # every 30 min
    only_on_change=True,
)
poster.start()
```

For cron-style one-shots, skip the autoposter and call `client.post_stats(...)` directly.

Async version is `AsyncAutoposter(async_client, ..., callback=async_fn)`.

## Vote webhooks

Register a URL TOP.TL will POST to whenever someone votes for your listing:

```python
client.set_webhook(
    "mybot",
    url="https://mybot.example.com/toptl-vote",
    reward_title="30-day premium",   # shown to the voter
)

# Send a test request to verify your endpoint
result = client.test_webhook("mybot")
print(result.success, result.status_code)
```

The webhook payload contains the voting user (`userId`, `firstName`, `username`), the listing, and a timestamp.

## Batch stats

Post stats for up to 25 listings in one request:

```python
client.batch_post_stats([
    {"username": "bot1", "member_count": 1200},
    {"username": "bot2", "member_count": 5400},
])
```

## Error handling

Every API error raises a subclass of `TopTLError`:

```python
from toptl import TopTL, AuthenticationError, NotFoundError, RateLimitError, ValidationError

try:
    client.post_stats("mybot", member_count=5000)
except AuthenticationError:
    ...  # bad key, or missing scope
except NotFoundError:
    ...  # listing does not exist
except RateLimitError:
    ...  # back off and retry
except ValidationError:
    ...  # payload rejected — see exc.response_body
```

## License

MIT — see `LICENSE`.
