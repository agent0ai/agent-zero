from helpers.api import ApiHandler, Request
from plugins._browser.helpers.runtime import suspend_runtime


class Stop(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        if not await suspend_runtime(if_idle=False):
            return {"ok": False, "error": "Browser is busy. Pause its chats and wait for browser actions and downloads to finish."}
        return {"ok": True}
