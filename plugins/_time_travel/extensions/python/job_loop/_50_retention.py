"""Throttled Time Travel retention sweep (see helpers/retention.py)."""

import asyncio
from typing import Any

from helpers.extension import Extension
from helpers.print_style import PrintStyle

_in_flight = False


class TimeTravelRetention(Extension):

    async def execute(self, **kwargs: Any) -> None:
        global _in_flight
        if _in_flight:
            return
        try:
            from plugins._time_travel.helpers import retention
        except Exception:
            return
        try:
            if not retention.due():
                return
            _in_flight = True
            try:
                stats = await asyncio.to_thread(retention.sweep)
            finally:
                _in_flight = False
            if any(stats.values()):
                PrintStyle().print(
                    "Time Travel retention: "
                    f"orphans={stats['orphans_removed']} aged={stats['aged_removed']} "
                    f"locks={stats['stale_locks_removed']} "
                    f"invalid={stats['invalid_backups_removed']} "
                    f"reclaimed={stats['bytes_reclaimed']}b"
                )
        except Exception:
            return
