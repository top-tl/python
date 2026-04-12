# toptl

[![PyPI version](https://img.shields.io/pypi/v/toptl.svg)](https://pypi.org/project/toptl/)
[![Python versions](https://img.shields.io/pypi/pyversions/toptl.svg)](https://pypi.org/project/toptl/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

Official Python SDK for [TOP.TL](https://top.tl) -- the Telegram directory.

## Installation

```bash
pip install toptl
```

For async support:

```bash
pip install toptl[async]
```

## Quick Start

```python
from toptl import TopTL

client = TopTL("toptl_xxx")

# Get a listing
listing = client.get_listing("mybot")
print(listing["title"], listing["votes"])

# Check votes
votes = client.get_votes("mybot", limit=10)
has_voted = client.has_voted("mybot", telegram_id=123456789)

# Post stats
client.post_stats("mybot", member_count=5000, group_count=120)

# Global stats
stats = client.get_stats()
print(stats["total_listings"])
```

## Webhooks

Set up a webhook to receive vote notifications in real time:

```python
# Configure the webhook URL
client.set_webhook("mybot", "https://example.com/webhook/votes")

# Optionally show a reward title after voting
client.set_webhook("mybot", "https://example.com/webhook/votes", reward_title="Premium for 24h")

# Send a test event to verify your endpoint
client.test_webhook("mybot")
```

## Batch Stats

Post stats for multiple listings in a single request:

```python
client.batch_post_stats([
    {"username": "bot_one", "memberCount": 5000, "groupCount": 120},
    {"username": "bot_two", "memberCount": 3200, "channelCount": 45},
])
```

## Auto-Post Stats

Automatically post stats in a background thread:

```python
from toptl import TopTL

client = TopTL("toptl_xxx")

# Auto-post stats every 30 min
client.start_autopost("mybot", lambda: {"member_count": get_user_count()})

# Only post when values actually change
client.start_autopost(
    "mybot",
    lambda: {"member_count": get_user_count()},
    only_on_change=True,
)

# ... your bot keeps running ...

# Stop when done
client.stop_autopost()
```

The autoposter also respects `retryAfter` from the server response -- if the
server tells you to wait longer, the next interval is adjusted automatically.

## Async Usage

```python
import asyncio
from toptl import AsyncTopTL

async def main():
    async with AsyncTopTL("toptl_xxx") as client:
        listing = await client.get_listing("mybot")
        print(listing["title"])

        await client.post_stats("mybot", member_count=5000)

        # Webhooks work the same way
        await client.set_webhook("mybot", "https://example.com/webhook")
        await client.test_webhook("mybot")

        # Batch stats
        await client.batch_post_stats([
            {"username": "bot_one", "memberCount": 5000},
            {"username": "bot_two", "memberCount": 3200},
        ])

asyncio.run(main())
```

## Aiogram Integration

Drop-in middleware for [aiogram](https://docs.aiogram.dev/) that tracks unique
chat IDs and auto-posts member count every 30 minutes:

```python
from aiogram import Bot, Dispatcher
from toptl import TopTL, aiogram_middleware

bot = Bot(token="BOT_TOKEN")
dp = Dispatcher()
client = TopTL("toptl_xxx")

# One line to wire it up
dp.message.middleware(aiogram_middleware(client, "mybot"))

if __name__ == "__main__":
    dp.run_polling(bot)
```

## python-telegram-bot Integration

Handler for [python-telegram-bot](https://python-telegram-bot.org/) that tracks
unique chats and posts stats automatically:

```python
from telegram.ext import ApplicationBuilder
from toptl import TopTL, ptb_handler

client = TopTL("toptl_xxx")
app = ApplicationBuilder().token("BOT_TOKEN").build()

# Add the tracking handler
app.add_handler(ptb_handler(client, "mybot"))

app.run_polling()
```

## Error Handling

```python
from toptl import TopTL, TopTLError

client = TopTL("toptl_xxx")

try:
    listing = client.get_listing("nonexistent")
except TopTLError as e:
    print(f"Error {e.status}: {e}")
    print(e.body)  # Raw error response
```

## API Reference

### `TopTL(token, *, base_url=None, timeout=15)`

Synchronous client.

| Method | Description |
|--------|-------------|
| `get_listing(username)` | Get listing info |
| `get_votes(username, *, limit=20)` | Get votes for a listing |
| `has_voted(username, telegram_id)` | Check if user voted |
| `post_stats(username, *, member_count=None, group_count=None)` | Post stats |
| `get_stats()` | Get global TOP.TL stats |
| `set_webhook(username, url, *, reward_title=None)` | Set vote webhook |
| `test_webhook(username)` | Send test webhook event |
| `batch_post_stats(stats)` | Post stats for multiple listings |
| `start_autopost(username, callback, *, interval=1800, only_on_change=False)` | Start autoposter |
| `stop_autopost()` | Stop autoposter |

### `AsyncTopTL(token, *, base_url=None, timeout=15)`

Async client with the same methods (all `await`-able). Supports `async with` context manager.

| Method | Description |
|--------|-------------|
| `close()` | Close the HTTP session |

### Framework helpers

| Function | Description |
|----------|-------------|
| `aiogram_middleware(client, username)` | Aiogram middleware for auto-posting stats |
| `ptb_handler(client, username)` | python-telegram-bot handler for auto-posting stats |

### Listing fields

| Field | Type | Description |
|-------|------|-------------|
| `username` | `str` | Telegram username |
| `title` | `str` | Listing title |
| `member_count` | `int` | Member/subscriber count |
| `group_count` | `int` | Number of groups the bot is in |
| `channel_count` | `int` | Number of channels |
| `bot_serves` | `int` | Number of users the bot serves |
| `votes` | `int` | Total votes received |

## License

MIT - see [LICENSE](LICENSE) for details.
