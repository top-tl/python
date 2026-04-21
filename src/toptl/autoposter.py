"""Autoposters — periodically call `post_stats` in the background.

Designed for long-running bot processes. For one-shot cron jobs, call
`TopTL.post_stats` directly instead.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from typing import Any, Awaitable, Callable

from .async_client import AsyncTopTL
from .client import TopTL

log = logging.getLogger("toptl.autoposter")


StatsCallback = Callable[[], dict[str, Any]]
AsyncStatsCallback = Callable[[], Awaitable[dict[str, Any]]]


class Autoposter:
    """Background thread that calls `client.post_stats` on an interval.

    Example:
        poster = Autoposter(
            client, "mybot",
            lambda: {"member_count": get_user_count()},
            interval_seconds=30 * 60,
            only_on_change=True,
        )
        poster.start()
        ...
        poster.stop()
    """

    def __init__(
        self,
        client: TopTL,
        username: str,
        callback: StatsCallback,
        *,
        interval_seconds: float = 30 * 60,
        only_on_change: bool = False,
        on_error: Callable[[BaseException], None] | None = None,
    ) -> None:
        self._client = client
        self._username = username
        self._callback = callback
        self._interval = float(interval_seconds)
        self._only_on_change = only_on_change
        self._on_error = on_error
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last: dict[str, Any] | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run, name=f"toptl-autopost:{self._username}", daemon=True
        )
        self._thread.start()

    def stop(self, timeout: float | None = 5) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=timeout)
            self._thread = None

    def post_once(self) -> None:
        """Run one cycle synchronously. Useful from inside a cron job."""
        self._tick()

    def _tick(self) -> None:
        try:
            stats = self._callback() or {}
        except Exception as err:
            self._handle_error(err)
            return
        if self._only_on_change and stats == self._last:
            return
        try:
            self._client.post_stats(self._username, **stats)
            self._last = dict(stats)
        except Exception as err:
            self._handle_error(err)

    def _run(self) -> None:
        while not self._stop.is_set():
            self._tick()
            # wait() returns True when stop() was called, so we can
            # exit immediately without waiting out the full interval.
            if self._stop.wait(self._interval):
                return

    def _handle_error(self, err: BaseException) -> None:
        if self._on_error:
            try:
                self._on_error(err)
                return
            except Exception:
                log.exception("on_error callback raised")
        log.warning("autopost tick failed: %s", err)


class AsyncAutoposter:
    """asyncio version of `Autoposter`. Runs as a cancellable task."""

    def __init__(
        self,
        client: AsyncTopTL,
        username: str,
        callback: AsyncStatsCallback,
        *,
        interval_seconds: float = 30 * 60,
        only_on_change: bool = False,
        on_error: Callable[[BaseException], None] | None = None,
    ) -> None:
        self._client = client
        self._username = username
        self._callback = callback
        self._interval = float(interval_seconds)
        self._only_on_change = only_on_change
        self._on_error = on_error
        self._task: asyncio.Task[None] | None = None
        self._last: dict[str, Any] | None = None

    def start(self) -> None:
        if self._task and not self._task.done():
            return
        loop = asyncio.get_event_loop()
        self._task = loop.create_task(self._run(), name=f"toptl-autopost:{self._username}")

    async def stop(self) -> None:
        if not self._task:
            return
        self._task.cancel()
        try:
            await self._task
        except (asyncio.CancelledError, Exception):
            pass
        self._task = None

    async def post_once(self) -> None:
        await self._tick()

    async def _tick(self) -> None:
        try:
            stats = (await self._callback()) or {}
        except Exception as err:
            self._handle_error(err)
            return
        if self._only_on_change and stats == self._last:
            return
        try:
            await self._client.post_stats(self._username, **stats)
            self._last = dict(stats)
        except Exception as err:
            self._handle_error(err)

    async def _run(self) -> None:
        try:
            while True:
                await self._tick()
                await asyncio.sleep(self._interval)
        except asyncio.CancelledError:
            raise

    def _handle_error(self, err: BaseException) -> None:
        if self._on_error:
            try:
                self._on_error(err)
                return
            except Exception:
                log.exception("on_error callback raised")
        log.warning("autopost tick failed: %s", err)
