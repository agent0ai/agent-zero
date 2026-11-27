import asyncio
from helpers.api import ApiHandler, Request
from plugins._desktop.helpers import runtime


class DesktopSession(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        action = str(input.get('action') or 'desktop')
        if action == 'status':
            return runtime.status()
        if action in {'desktop', 'open', 'session'}:
            await asyncio.to_thread(runtime.start)
            return runtime.status()
        if action == 'shutdown':
            await asyncio.to_thread(runtime.stop)
            return runtime.status()
        return {'ok': False, 'error': 'Unsupported Desktop action'}
