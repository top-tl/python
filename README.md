# toptl

[![PyPI version](https://img.shields.io/pypi/v/toptl.svg)](https://pypi.org/project/toptl/)
[![Python versions](https://img.shields.io/pypi/pyversions/toptl.svg)](https://pypi.org/project/toptl/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

Official Python SDK for [TOP.TL](https://top.tl) — the Telegram directory.

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

## Auto-Post Stats

Automatically post stats every 30 minutes in a background thread:

```python
from toptl import TopTL

client = TopTL("toptl_xxx")

# Auto-post stats every 30 min
client.start_autopost("mybot", lambda: {"member_count": get_user_count()})

# ... your bot keeps running ...

# Stop when done
client.stop_autopost()
```

## Async Usage

```python
import asyncio
from toptl import AsyncTopTL

async def main():
    async with AsyncTopTL("toptl_xxx") as client:
        listing = await client.get_listing("mybot")
        print(listing["title"])

        await client.post_stats("mybot", member_count=5000)

asyncio.run(main())
```

## Aiogram Integration

```python
from aiogram import Bot, Dispatcher
from toptl import TopTL

bot = Bot(token="BOT_TOKEN")
dp = Dispatcher()
toptl = TopTL("toptl_xxx")

# Auto-post member count every 30 minutes
async def get_stats():
    count = await bot.get_chat_member_count("@mychannel")
    return {"member_count": count}

toptl.start_autopost("mybot", lambda: {
    "member_count": 0  # replace with your actual count logic
})

# Or post manually after events
@dp.message()
async def on_message(message):
    # ... handle message ...
    pass

if __name__ == "__main__":
    dp.run_polling(bot)
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
| `start_autopost(username, callback, *, interval=1800)` | Start autoposter |
| `stop_autopost()` | Stop autoposter |

### `AsyncTopTL(token, *, base_url=None, timeout=15)`

Async client with the same methods (all `await`-able). Supports `async with` context manager.

| Method | Description |
|--------|-------------|
| `close()` | Close the HTTP session |

## License

MIT - see [LICENSE](LICENSE) for details.
