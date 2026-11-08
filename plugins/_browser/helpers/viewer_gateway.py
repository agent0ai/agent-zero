"""Authenticated noVNC assets and a binary WebSocket bridge to owned loopback displays."""
import asyncio
import contextlib
from pathlib import Path
from urllib.parse import urlsplit

from starlette.responses import FileResponse, JSONResponse, PlainTextResponse
from starlette.websockets import WebSocket, WebSocketDisconnect

from helpers import plugins, virtual_desktop
from helpers.virtual_desktop_routes import VirtualDesktopGateway

ASSETS = Path(__file__).resolve().parents[1] / 'webui'


class BrowserVncGateway(VirtualDesktopGateway):
    def __init__(self, flask_app):
        super().__init__(flask_app, '/browser/vnc')

    def allowed(self, scope):
        if plugins.get_toggle_state('_browser') != 'enabled' or not self.is_authorized(scope):
            return False
        headers = dict(scope.get('headers', []))
        if headers.get(b'sec-fetch-site', b'').lower() in {b'cross-site', b'same-site'}:
            return False
        origin = headers.get(b'origin', b'').decode('latin-1')
        if origin:
            try:
                parsed = urlsplit(origin)
            except ValueError:
                return False
            if parsed.scheme not in {'http', 'https'} or parsed.netloc.lower() != headers.get(b'host', b'').decode('latin-1').lower():
                return False
        elif scope['type'] == 'websocket':
            return False
        return True

    def endpoint(self, scope):
        route = self.session_request(self.relative_path(scope))
        if not route:
            return None, ''
        endpoint = virtual_desktop.proxy_for_token(route[0])
        if not endpoint or endpoint.owner != 'browser-vnc' or endpoint.host != '127.0.0.1':
            return None, ''
        return endpoint, route[1]

    async def http(self, scope, receive, send):
        if not self.allowed(scope):
            await PlainTextResponse('Access denied', status_code=403)(scope, receive, send)
            return
        endpoint, path = self.endpoint(scope)
        headers = {'Cache-Control': 'no-store', 'X-Frame-Options': 'SAMEORIGIN', 'X-Content-Type-Options': 'nosniff'}
        if not endpoint or scope.get('method') not in {'GET', 'HEAD'}:
            response = PlainTextResponse('Browser viewer not found', status_code=404)
        elif path == '/credentials':
            response = JSONResponse({'password': endpoint.password}, headers=headers)
        else:
            if path == '/index.html':
                asset = ASSETS / 'vnc.html'
            elif path == '/vnc.js':
                asset = ASSETS / 'vnc.js'
            elif path.startswith('/vendor/novnc/'):
                asset = (ASSETS / path.lstrip('/')).resolve()
                if not asset.is_relative_to((ASSETS / 'vendor/novnc').resolve()):
                    asset = None
            else:
                asset = None
            response = FileResponse(asset, headers=headers) if asset and asset.is_file() else PlainTextResponse('Not found', status_code=404)
        await response(scope, receive, send)

    async def websocket(self, scope, receive, send):
        socket = WebSocket(scope, receive=receive, send=send)
        endpoint, path = self.endpoint(scope)
        if not self.allowed(scope) or not endpoint or path != '/ws':
            await socket.close(code=1008)
            return
        writer = None
        tasks = []
        try:
            reader, writer = await asyncio.wait_for(asyncio.open_connection(endpoint.host, endpoint.port), 10)
            await socket.accept()

            async def to_display():
                while True:
                    message = await socket.receive()
                    if message['type'] == 'websocket.disconnect':
                        return
                    data = message.get('bytes')
                    if data is None or len(data) > 1024 * 1024:
                        await socket.close(code=1009)
                        return
                    writer.write(data)
                    await writer.drain()

            async def to_browser():
                while data := await reader.read(65536):
                    await socket.send_bytes(data)

            tasks = [asyncio.create_task(to_display()), asyncio.create_task(to_browser())]
            done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                task.result()
        except (OSError, TimeoutError, RuntimeError, WebSocketDisconnect):
            pass
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            if writer:
                writer.close()
                with contextlib.suppress(OSError):
                    await writer.wait_closed()
            with contextlib.suppress(RuntimeError, OSError, WebSocketDisconnect):
                await socket.close()
