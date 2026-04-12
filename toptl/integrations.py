"""Framework integrations for aiogram and python-telegram-bot."""

import asyncio
import logging
from typing import Any, Callable, Set

logger = logging.getLogger("toptl.integrations")


def aiogram_middleware(client: Any, username: str) -> Any:
    """Return an aiogram-compatible middleware that tracks unique chat IDs
    and auto-posts stats to TOP.TL.

    Usage::

        from toptl import TopTL, aiogram_middleware

        client = TopTL("toptl_xxx")
        dp.message.middleware(aiogram_middleware(client, "mybot"))

    The middleware counts distinct ``chat.id`` values seen across all
    incoming messages and periodically posts that as ``member_count``.

    Args:
        client: A :class:`TopTL` or :class:`AsyncTopTL` instance.
        username: The listing username to post stats for.

    Returns:
        An aiogram ``BaseMiddleware`` subclass instance.
    """
    try:
        from aiogram import BaseMiddleware
        from aiogram.types import TelegramObject
    except ImportError:
        raise ImportError(
            "aiogram is required for aiogram_middleware. "
            "Install it with: pip install aiogram"
        )

    class TopTLMiddleware(BaseMiddleware):
        def __init__(self) -> None:
            super().__init__()
            self._chat_ids: Set[int] = set()
            self._post_task: Any = None
            self._started = False

        async def __call__(
            self,
            handler: Callable,
            event: TelegramObject,
            data: dict,
        ) -> Any:
            # Track unique chat IDs
            if hasattr(event, "chat") and event.chat is not None:
                self._chat_ids.add(event.chat.id)

            # Start the background posting loop on first message
            if not self._started:
                self._started = True
                self._post_task = asyncio.ensure_future(self._post_loop())

            return await handler(event, data)

        async def _post_loop(self) -> None:
            """Post stats every 30 minutes."""
            while True:
                await asyncio.sleep(1800)
                try:
                    count = len(self._chat_ids)
                    if hasattr(client, "post_stats") and asyncio.iscoroutinefunction(
                        getattr(client, "post_stats", None)
                    ):
                        await client.post_stats(username, member_count=count)
                    else:
                        client.post_stats(username, member_count=count)
                    logger.debug(
                        "aiogram middleware posted member_count=%d for @%s",
                        count,
                        username,
                    )
                except Exception:
                    logger.exception(
                        "aiogram middleware failed to post stats for @%s", username
                    )

    return TopTLMiddleware()


def ptb_handler(client: Any, username: str) -> Any:
    """Return a python-telegram-bot handler that tracks unique chat IDs
    and auto-posts stats to TOP.TL.

    Usage::

        from toptl import TopTL, ptb_handler

        client = TopTL("toptl_xxx")
        application.add_handler(ptb_handler(client, "mybot"))

    The handler listens to all messages via a ``MessageHandler`` with
    ``filters.ALL``, counts distinct ``chat.id`` values, and posts
    ``member_count`` every 30 minutes.

    Args:
        client: A :class:`TopTL` or :class:`AsyncTopTL` instance.
        username: The listing username to post stats for.

    Returns:
        A python-telegram-bot ``MessageHandler`` instance.
    """
    try:
        from telegram.ext import MessageHandler, ContextTypes, filters
    except ImportError:
        raise ImportError(
            "python-telegram-bot is required for ptb_handler. "
            "Install it with: pip install python-telegram-bot"
        )

    chat_ids: Set[int] = set()
    _job_scheduled = False

    async def _post_stats(context: Any) -> None:
        """Job callback: post stats to TOP.TL."""
        try:
            count = len(chat_ids)
            if hasattr(client, "post_stats") and asyncio.iscoroutinefunction(
                getattr(client, "post_stats", None)
            ):
                await client.post_stats(username, member_count=count)
            else:
                client.post_stats(username, member_count=count)
            logger.debug(
                "ptb handler posted member_count=%d for @%s", count, username
            )
        except Exception:
            logger.exception(
                "ptb handler failed to post stats for @%s", username
            )

    async def _track_message(update: Any, context: Any) -> None:
        """Track the chat ID from every incoming message."""
        nonlocal _job_scheduled
        if update.effective_chat is not None:
            chat_ids.add(update.effective_chat.id)

        # Schedule the repeating job on the first message
        if not _job_scheduled and context.job_queue is not None:
            context.job_queue.run_repeating(
                _post_stats, interval=1800, first=1800, name="toptl_stats"
            )
            _job_scheduled = True

    return MessageHandler(filters.ALL, _track_message, block=False)
