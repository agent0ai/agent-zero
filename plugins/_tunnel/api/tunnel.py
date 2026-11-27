import asyncio
from helpers.api import ApiHandler, Request
from helpers.sandbox import SandboxError
from plugins._tunnel.helpers import runtime


class Tunnel(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        return await process(input)


async def process(input: dict) -> dict:
    try:
        return await asyncio.to_thread(runtime.request, input)
    except (SandboxError, ValueError, OSError) as exc:
        return {'success': False, 'message': str(exc)}
