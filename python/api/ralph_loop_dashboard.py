"""
API endpoint for the Ralph Loop Dashboard UI.
Provides aggregated data for loop stats, active loops, and recent completions.
"""

import os
from datetime import datetime, timezone

from python.helpers import files
from python.helpers.api import ApiHandler, Request, Response


class RalphLoopDashboard(ApiHandler):
    """API handler for the Ralph Loop dashboard."""

    # Consider "active" loops stale if they had no activity for this window.
    # This prevents abandoned/test loops from showing as currently running.
    STALE_ACTIVE_WINDOW_HOURS = 6

    def _parse_ts(self, value: str | None) -> datetime | None:
        if not value:
            return None
        raw = str(value).strip()
        if not raw:
            return None
        try:
            normalized = raw.replace("Z", "+00:00")
            dt = datetime.fromisoformat(normalized)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            # Handles sqlite CURRENT_TIMESTAMP format: "YYYY-MM-DD HH:MM:SS"
            try:
                dt = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
                return dt.replace(tzinfo=timezone.utc)
            except Exception:
                return None

    def _is_live_active_loop(self, manager, loop: dict, now_utc: datetime) -> bool:
        if loop.get("status") != "active":
            return False

        timestamps: list[datetime] = []
        started = self._parse_ts(loop.get("started_at"))
        if started:
            timestamps.append(started)

        try:
            iterations = manager.get_iteration_history(loop.get("loop_id")) or []
            if iterations:
                latest = iterations[-1]
                latest_started = self._parse_ts(latest.get("started_at"))
                latest_completed = self._parse_ts(latest.get("completed_at"))
                if latest_started:
                    timestamps.append(latest_started)
                if latest_completed:
                    timestamps.append(latest_completed)
        except Exception:
            pass

        if not timestamps:
            return True

        last_activity = max(timestamps)
        age_hours = (now_utc - last_activity).total_seconds() / 3600.0
        return age_hours < self.STALE_ACTIVE_WINDOW_HOURS

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            # Import the Ralph Loop manager
            from instruments.custom.ralph_loop.ralph_manager import RalphLoopManager

            # Get database path
            db_path = files.get_abs_path("./instruments/custom/ralph_loop/data/ralph_loop.db")

            # Ensure data directory exists
            data_dir = os.path.dirname(db_path)
            if not os.path.exists(data_dir):
                os.makedirs(data_dir, exist_ok=True)

            # Initialize manager
            manager = RalphLoopManager(db_path)

            # Get statistics
            stats = manager.get_stats()

            # Get active loops and filter out stale ones so UI reflects currently running work.
            now_utc = datetime.now(timezone.utc)
            active_candidates = manager.list_loops(status="active", limit=20)
            active_loops = [loop for loop in active_candidates if self._is_live_active_loop(manager, loop, now_utc)]
            stale_active_loops = max(0, len(active_candidates) - len(active_loops))

            # Get recent completed/cancelled loops
            recent_completed = manager.list_loops(status="completed", limit=10)
            recent_cancelled = manager.list_loops(status="cancelled", limit=5)
            recent_max_iter = manager.list_loops(status="max_iterations", limit=5)

            # Combine recent loops and sort by completed_at/started_at
            recent_loops = recent_completed + recent_cancelled + recent_max_iter
            recent_loops.sort(key=lambda x: x.get("completed_at") or x.get("started_at") or "", reverse=True)
            recent_loops = recent_loops[:10]

            # Calculate success rate
            total_completed = stats.get("completed_loops", 0)
            total_cancelled = stats.get("cancelled_loops", 0)
            total_finished = total_completed + total_cancelled
            success_rate = round((total_completed / total_finished) * 100, 1) if total_finished > 0 else 0

            return {
                "success": True,
                "stats": {
                    "total_loops": stats.get("total_loops", 0),
                    "active_loops": len(active_loops),
                    "completed_loops": stats.get("completed_loops", 0),
                    "cancelled_loops": stats.get("cancelled_loops", 0),
                    "max_iterations_loops": stats.get("max_iterations_loops", 0),
                    "paused_loops": stats.get("paused_loops", 0),
                    "stale_active_loops": stale_active_loops,
                    "total_iterations": stats.get("total_iterations", 0),
                    "avg_iterations_per_loop": stats.get("avg_iterations_per_loop", 0),
                    "success_rate": success_rate,
                },
                "active_loops": active_loops,
                "recent_loops": recent_loops,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stats": {
                    "total_loops": 0,
                    "active_loops": 0,
                    "completed_loops": 0,
                    "cancelled_loops": 0,
                    "max_iterations_loops": 0,
                    "paused_loops": 0,
                    "total_iterations": 0,
                    "avg_iterations_per_loop": 0,
                    "success_rate": 0,
                },
                "active_loops": [],
                "recent_loops": [],
            }
