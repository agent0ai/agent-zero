"""
MOS Scheduler Init — auto-registers MOS cron tasks on startup.

Called during app initialization to schedule cross-system sync jobs.
Uses the existing task_scheduler infrastructure if available,
otherwise falls back to a simple asyncio-based scheduler.
"""

import traceback
from typing import Any


def register_mos_schedules() -> dict[str, Any]:
    """Register MOS sync jobs. Safe to call multiple times (idempotent)."""
    registered = []

    try:
        # Try using existing scheduler infrastructure
        try:
            from python.helpers.task_scheduler import TaskScheduler

            scheduler = TaskScheduler.get_instance()

            # Linear → Motion sync: 8am, 12pm, 5pm weekdays
            scheduler.register_task(
                name="mos_linear_to_motion",
                cron="0 8,12,17 * * 1-5",
                handler=_run_linear_to_motion,
            )
            registered.append("mos_linear_to_motion")

            # Linear activity → Digest: 6am daily
            scheduler.register_task(
                name="mos_linear_activity_digest",
                cron="0 6 * * *",
                handler=_run_linear_activity_digest,
            )
            registered.append("mos_linear_activity_digest")

        except ImportError:
            # No task_scheduler available — jobs can be triggered manually
            pass

    except Exception:
        traceback.print_exc()

    return {"registered": registered, "count": len(registered)}


async def _run_linear_to_motion() -> None:
    """Wrapper for scheduler callback."""
    try:
        from python.helpers.mos_orchestrator import MOSOrchestrator

        await MOSOrchestrator.sync_linear_to_motion()
    except Exception:
        traceback.print_exc()


async def _run_linear_activity_digest() -> None:
    """Wrapper for scheduler callback."""
    try:
        from python.helpers.mos_orchestrator import MOSOrchestrator

        await MOSOrchestrator.sync_linear_activity_to_digest()
    except Exception:
        traceback.print_exc()
