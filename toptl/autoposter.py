"""Background thread autoposter for TOP.TL stats."""

import threading
import logging
from typing import TYPE_CHECKING, Callable, Dict, Optional, Union

if TYPE_CHECKING:
    from .client import TopTL

logger = logging.getLogger("toptl.autoposter")


class AutoPoster:
    """Posts stats to TOP.TL on a recurring interval using a background thread.

    Args:
        client: The TopTL client instance.
        username: The listing username to post stats for.
        callback: A callable that returns a dict with ``member_count``
            and/or ``group_count`` keys.
        interval: Seconds between posts. Defaults to 1800 (30 minutes).
    """

    def __init__(
        self,
        client: "TopTL",
        username: str,
        callback: Callable[[], Dict[str, Optional[int]]],
        interval: int = 1800,
    ) -> None:
        self._client = client
        self._username = username
        self._callback = callback
        self._interval = interval
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the autoposter background thread."""
        if self._thread is not None and self._thread.is_alive():
            raise RuntimeError("AutoPoster is already running")

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info(
            "AutoPoster started for @%s every %ds", self._username, self._interval
        )

    def stop(self) -> None:
        """Stop the autoposter background thread."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None
        logger.info("AutoPoster stopped for @%s", self._username)

    @property
    def running(self) -> bool:
        """Whether the autoposter is currently running."""
        return self._thread is not None and self._thread.is_alive()

    def _run(self) -> None:
        """Internal loop: post stats, then wait for the interval or stop signal."""
        while not self._stop_event.is_set():
            try:
                stats = self._callback()
                self._client.post_stats(
                    self._username,
                    member_count=stats.get("member_count"),
                    group_count=stats.get("group_count"),
                )
                logger.debug("Posted stats for @%s: %s", self._username, stats)
            except Exception:
                logger.exception("AutoPoster error for @%s", self._username)

            self._stop_event.wait(self._interval)
