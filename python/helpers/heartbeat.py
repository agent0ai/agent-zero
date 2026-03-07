"""Heartbeat daemon with cron-based and event-driven trigger support.

The daemon runs a 30-minute cron loop that parses ``HEARTBEAT.md`` checklists.
It also integrates with the :class:`EventBus` so that registered triggers can
fire in response to system events, conditions, or message patterns.
"""

from __future__ import annotations

import asyncio
import os
import re
from typing import Any

from python.helpers import files
from python.helpers.event_bus import EventBus  # noqa: TCH001
from python.helpers.event_triggers import (
    HeartbeatTrigger,
    TriggerStore,
    TriggerType,
    evaluate_condition_trigger,
    evaluate_event_trigger,
    evaluate_message_trigger,
)
from python.helpers.print_style import PrintStyle

# Default cron interval in seconds (30 minutes)
HEARTBEAT_INTERVAL_SECONDS = 30 * 60

_HEARTBEAT_MD_PATH = "HEARTBEAT.md"


# ---------------------------------------------------------------------------
# Heartbeat checklist parser
# ---------------------------------------------------------------------------


def parse_heartbeat_md(path: str | None = None) -> list[dict[str, Any]]:
    """Parse ``HEARTBEAT.md`` and return a list of checklist items.

    Each item is a dict with keys ``done`` (bool) and ``text`` (str).
    """
    abs_path = files.get_abs_path(path or _HEARTBEAT_MD_PATH)
    if not os.path.isfile(abs_path):
        return []
    items: list[dict[str, Any]] = []
    with open(abs_path, encoding="utf-8") as fh:
        for line in fh:
            m = re.match(r"^\s*-\s*\[([ xX])\]\s*(.*)", line)
            if m:
                items.append({"done": m.group(1).lower() == "x", "text": m.group(2).strip()})
    return items


# ---------------------------------------------------------------------------
# HeartbeatDaemon
# ---------------------------------------------------------------------------


class HeartbeatDaemon:
    """Manages both the periodic cron loop and event-driven triggers.

    Usage::

        bus = EventBus(EventStore("events.db"))
        daemon = HeartbeatDaemon(bus)
        await daemon.start()
    """

    def __init__(
        self,
        event_bus: EventBus,
        trigger_store: TriggerStore | None = None,
        interval: int = HEARTBEAT_INTERVAL_SECONDS,
    ):
        self.event_bus = event_bus
        self.trigger_store = trigger_store or TriggerStore()
        self.interval = interval
        self._running = False
        self._cron_task: asyncio.Task | None = None
        self._trigger_task: asyncio.Task | None = None

        # Wire up event-bus listener so EVENT triggers fire automatically
        self.event_bus.subscribe("*", self._on_event)

    # -- public API ---------------------------------------------------------

    async def start(self) -> None:
        """Start the cron loop and trigger evaluation loop."""
        if self._running:
            return
        self._running = True
        self._cron_task = asyncio.ensure_future(self._cron_loop())
        self._trigger_task = asyncio.ensure_future(self._condition_loop())
        PrintStyle(font_color="green").print("[Heartbeat] daemon started")

    async def stop(self) -> None:
        """Gracefully stop both loops."""
        self._running = False
        for task in (self._cron_task, self._trigger_task):
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        PrintStyle(font_color="yellow").print("[Heartbeat] daemon stopped")

    def register_trigger(self, trigger: HeartbeatTrigger) -> None:
        """Persist a new trigger."""
        self.trigger_store.save(trigger)

    def evaluate_triggers(
        self,
        *,
        event_type: str | None = None,
        payload: dict | None = None,
        metrics: dict | None = None,
        message: str | None = None,
    ) -> list[HeartbeatTrigger]:
        """Evaluate all triggers against the provided context and return those that matched."""
        matched: list[HeartbeatTrigger] = []
        for trigger in self.trigger_store.list_all():
            if not trigger.enabled:
                continue
            hit = False
            if trigger.type == TriggerType.EVENT and event_type:
                hit = evaluate_event_trigger(trigger, event_type, payload or {})
            elif trigger.type == TriggerType.CONDITION and metrics:
                hit = evaluate_condition_trigger(trigger, metrics)
            elif trigger.type == TriggerType.MESSAGE and message:
                hit = evaluate_message_trigger(trigger, message)
            if hit:
                matched.append(trigger)
                self.trigger_store.update_last_triggered(trigger.id)
        return matched

    async def handle_event(self, event_type: str, payload: dict[str, Any]) -> list[HeartbeatTrigger]:
        """Evaluate event-type triggers and execute matched items."""
        matched = self.evaluate_triggers(event_type=event_type, payload=payload)
        for trigger in matched:
            await self._execute_items(trigger)
        return matched

    # -- internal loops -----------------------------------------------------

    async def _cron_loop(self) -> None:
        """30-minute heartbeat cron: parse HEARTBEAT.md and execute pending items."""
        while self._running:
            try:
                items = parse_heartbeat_md()
                pending = [i for i in items if not i["done"]]
                if pending:
                    PrintStyle(font_color="cyan").print(f"[Heartbeat] cron tick: {len(pending)} pending items")
                # Also evaluate CRON-type triggers
                for trigger in self.trigger_store.list_all():
                    if trigger.type == TriggerType.CRON and trigger.enabled:
                        self.trigger_store.update_last_triggered(trigger.id)
                        await self._execute_items(trigger)
            except Exception as exc:
                PrintStyle.error(f"[Heartbeat] cron error: {exc}")
            await asyncio.sleep(self.interval)

    async def _condition_loop(self) -> None:
        """Periodically evaluate CONDITION triggers (every 60s)."""
        while self._running:
            try:
                metrics = self._collect_metrics()
                self.evaluate_triggers(metrics=metrics)
            except Exception as exc:
                PrintStyle.error(f"[Heartbeat] condition eval error: {exc}")
            await asyncio.sleep(60)

    # -- helpers ------------------------------------------------------------

    async def _on_event(self, event: dict[str, Any]) -> None:
        """EventBus wildcard handler — route to trigger evaluation."""
        event_type = event.get("type", "")
        payload = event.get("payload", {})
        await self.handle_event(event_type, payload)

    async def _execute_items(self, trigger: HeartbeatTrigger) -> None:
        """Execute the heartbeat items attached to a trigger."""
        for item in trigger.items:
            PrintStyle(font_color="white").print(
                f"[Heartbeat] executing trigger={trigger.id} item={item.get('text', item)}"
            )

    @staticmethod
    def _collect_metrics() -> dict[str, Any]:
        """Collect system metrics for condition trigger evaluation."""
        import psutil  # type: ignore[import-untyped]

        try:
            mem = psutil.virtual_memory()
            return {
                "memory_percent": mem.percent,
                "cpu_percent": psutil.cpu_percent(interval=0.1),
            }
        except Exception:
            return {}
