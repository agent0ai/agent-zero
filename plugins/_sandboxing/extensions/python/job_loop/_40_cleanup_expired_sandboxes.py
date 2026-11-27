from __future__ import annotations

import asyncio
import datetime as dt

from helpers.extension import Extension
from helpers.print_style import PrintStyle
from plugins._sandboxing.helpers.runtime import get_manager


class CleanupExpiredSandboxes(Extension):
    _last_check: dt.datetime | None = None

    async def execute(self, **kwargs) -> None:
        now = dt.datetime.now(dt.timezone.utc)
        last_check = type(self)._last_check
        if last_check and now - last_check < dt.timedelta(hours=1):
            return
        type(self)._last_check = now
        try:
            manager = get_manager()
            deleted = await asyncio.to_thread(manager.cleanup_expired, now=now)
            deleted_images = await asyncio.to_thread(manager.cleanup_images, now=now)
            if deleted:
                PrintStyle.info("Deleted expired temporary sandboxes:", deleted)
            if deleted_images:
                PrintStyle.info("Deleted old unused sandbox images:", deleted_images)
        except Exception as exc:
            PrintStyle.warning("Sandbox and image cleanup failed:", exc)
