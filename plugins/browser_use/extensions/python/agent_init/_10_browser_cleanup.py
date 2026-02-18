"""Clean up orphaned browser sessions on agent init/reset."""

from python.helpers.extension import Extension


class BrowserCleanup(Extension):
    async def execute(self, **kwargs):
        from plugins.browser_use.helpers.session_manager import SessionManager

        manager = SessionManager.get_existing(self.agent)
        if manager:
            await manager.close()
