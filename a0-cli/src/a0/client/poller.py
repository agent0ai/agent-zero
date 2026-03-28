"""Agent Zero log poller.

Uses /api_log_get to fetch log items and track changes
via log guid (detects context resets).
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Callable

from a0.client.api import AgentZeroClient, LogItem, LogResponse


@dataclass
class PollState:
    """Tracks polling state for a context."""

    context_id: str
    last_total: int = 0
    log_guid: str = ""


@dataclass
class PollEvent:
    """A single event from the poll loop."""

    logs: list[dict[str, Any]] = field(default_factory=list)
    progress: str | int = 0
    progress_active: bool = False
    context_reset: bool = False


class Poller:
    """Polls /api_log_get for new log items.

    Usage:
        async for event in poller.stream(context_id):
            for log in event.logs:
                print(log["type"], log["content"])
    """

    def __init__(
        self,
        client: AgentZeroClient,
        interval: float = 0.5,
    ) -> None:
        self.client = client
        self.interval = interval
        self._states: dict[str, PollState] = {}
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    async def poll_once(self, context_id: str) -> PollEvent:
        """Execute a single poll and return new items."""
        state = self._states.setdefault(context_id, PollState(context_id=context_id))

        response = await self.client.get_logs(context_id=context_id, length=200)
        log = response.log

        context_reset = False
        if log.guid and log.guid != state.log_guid:
            if state.log_guid:  # not first poll
                context_reset = True
                state.last_total = 0
            state.log_guid = log.guid

        # Only return items we haven't seen
        new_items = []
        if log.total_items > state.last_total:
            # Items are returned newest-first from start_position
            # We want only items after our last known total
            skip = state.last_total - log.start_position
            if skip < 0:
                skip = 0
            new_items = log.items[skip:]

        state.last_total = log.total_items

        return PollEvent(
            logs=new_items,
            progress=log.progress,
            progress_active=log.progress_active,
            context_reset=context_reset,
        )

    async def stream(
        self,
        context_id: str,
        stop_when: Callable[[PollEvent], bool] | None = None,
    ) -> AsyncIterator[PollEvent]:
        """Stream poll events for a context."""
        self._stop = False

        while not self._stop:
            try:
                event = await self.poll_once(context_id)
            except Exception:
                await asyncio.sleep(self.interval)
                continue

            yield event

            if stop_when and stop_when(event):
                break

            await asyncio.sleep(self.interval)
