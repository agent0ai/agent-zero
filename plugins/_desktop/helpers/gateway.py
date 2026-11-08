"""Streaming Tuxee proxy behind the existing WebUI login, with no client-selected upstream."""
import asyncio
import contextlib
from http.cookies import SimpleCookie
import time
from urllib.parse import urlsplit
import aiohttp
from starlette.requests import HTTPConnection, Request
from starlette.responses import PlainTextResponse
from starlette.websockets import WebSocket, WebSocketDisconnect
from helpers import dotenv, plugins, runtime as framework_runtime
from helpers.virtual_desktop_routes import VirtualDesktopGateway
from plugins._desktop.helpers import runtime

PREFIX = '/desktop/tuxee'
MANUAL_COOKIE = 'a0_tuxee_manual'
HOP = {'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization', 'te', 'trailer', 'transfer-encoding', 'upgrade'}
REQUEST_HEADERS = {'host', 'origin', 'content-type', 'content-length', 'accept', 'accept-language', 'range',
                   'if-range', 'if-none-match', 'if-modified-since', 'x-tuxee-csrf', 'x-tuxee-client', 'x-tuxee-size', 'sec-fetch-site'}


class TuxeeGateway(VirtualDesktopGateway):
    def __init__(self, flask_app):
        super().__init__(flask_app, PREFIX)
        self._login_lock = asyncio.Lock()
        self._login_port = 0
        self._login_cookie = ''
        self._retry_after = 0

    async def auto_login(self, session, port, password):
        async with self._login_lock:
            if self._login_port != port:
                self._login_port = port
                self._login_cookie = ''
                self._retry_after = 0
            base = f'http://127.0.0.1:{port}'
            headers = {'origin': base, 'x-tuxee-client': 'web'}
            try:
                async with asyncio.timeout(20):
                    if self._login_cookie:
                        async with session.get(base + '/api/connection',
                                               headers={**headers, 'cookie': self._login_cookie},
                                               allow_redirects=False) as response:
                            state = await response.json() if response.status == 200 else None
                            if isinstance(state, dict) and state.get('authenticated') is True:
                                return
                        self._login_cookie = ''
                    if time.monotonic() < self._retry_after:
                        return
                    # A failed PAM login must not be retried by every iframe reload.
                    self._retry_after = time.monotonic() + 60
                    async with session.post(base + '/api/login', headers=headers,
                                            json={'username': 'root', 'password': password},
                                            allow_redirects=False) as response:
                        if response.status == 200:
                            self._login_cookie = '; '.join(f'{name}={cookie.coded_value}'
                                for name, cookie in response.cookies.items()
                                if name.startswith('tuxee_session_') and cookie.value)
                            if self._login_cookie:
                                self._retry_after = 0
            except (aiohttp.ClientError, TimeoutError, ValueError):
                self._login_cookie = ''
                self._retry_after = time.monotonic() + 60

    def allowed(self, scope):
        if plugins.get_toggle_state('_desktop') != 'enabled' or not self.is_authorized(scope):
            return False
        headers = dict(scope.get('headers', []))
        if headers.get(b'sec-fetch-site', b'').lower() in {b'cross-site', b'same-site'}:
            return False
        origin = headers.get(b'origin', b'').decode('latin-1')
        if origin:
            parsed = urlsplit(origin)
            if parsed.scheme not in {'http', 'https'} or parsed.netloc.lower() != headers.get(b'host', b'').decode('latin-1').lower():
                return False
        elif scope['type'] == 'websocket' or scope.get('method', 'GET') not in {'GET', 'HEAD'}:
            return False
        return True

    def upstream_headers(self, scope):
        result = {key.decode('latin-1'): value.decode('latin-1') for key, value in scope.get('headers', [])
                  if key.decode('latin-1') in REQUEST_HEADERS}
        cookies = SimpleCookie()
        cookies.load(dict(scope.get('headers', [])).get(b'cookie', b'').decode('latin-1'))
        result['cookie'] = '; '.join(f'{name}={cookie.coded_value}' for name, cookie in cookies.items()
                                    if name.startswith(('tuxee_session_', 'tuxee_language_')))
        # Forward only transport context derived from this accepted request.
        result['x-forwarded-proto'] = 'https' if scope.get('scheme') in {'https', 'wss'} or result.get('origin', '').startswith('https://') else 'http'
        return result

    async def __call__(self, scope, receive, send):
        websocket = scope['type'] == 'websocket'
        if not self.allowed(scope):
            if websocket:
                await WebSocket(scope, receive, send).close(code=1008)
            else:
                await PlainTextResponse('Desktop authentication or origin check failed', status_code=403)(scope, receive, send)
            return
        path = self.relative_path(scope)
        if path == '/api/update/apply':
            await PlainTextResponse('This Tuxee runtime is updated with Agent Zero', status_code=409)(scope, receive, send)
            return
        try:
            port = await asyncio.to_thread(runtime.start)
            query = scope.get('query_string', b'').decode('latin-1')
            url = f'http://127.0.0.1:{port}{path}' + ('?' + query if query else '')
            timeout = aiohttp.ClientTimeout(total=None, sock_connect=10)
            async with aiohttp.ClientSession(timeout=timeout, auto_decompress=False,
                                             cookie_jar=aiohttp.DummyCookieJar()) as session:
                upstream_headers = self.upstream_headers(scope)
                cookies = HTTPConnection(scope).cookies
                manual = MANUAL_COOKIE in cookies or any(name.startswith('tuxee_session_') for name in cookies)
                auto_cookie = ''
                if not manual and framework_runtime.is_dockerized():
                    password = dotenv.get_dotenv_value(dotenv.KEY_ROOT_PASSWORD)
                    if password:
                        if not websocket and scope['method'] == 'GET' and path in {'/', '/index.html'}:
                            await self.auto_login(session, port, password)
                        if self._login_port == port:
                            auto_cookie = self._login_cookie
                            upstream_headers['cookie'] = '; '.join(filter(None, [upstream_headers['cookie'], auto_cookie]))
                if websocket:
                    await self.proxy_socket(session, url, scope, receive, send, upstream_headers)
                else:
                    request = Request(scope, receive)
                    async with session.request(scope['method'], url, headers=upstream_headers,
                                               data=request.stream(), allow_redirects=False) as response:
                        headers = []
                        for raw_name, raw_value in response.raw_headers:
                            name, value = raw_name.decode('latin-1').lower(), raw_value.decode('latin-1')
                            if name in HOP:
                                continue
                            if name == 'x-frame-options':
                                value = 'SAMEORIGIN'
                            elif name == 'content-security-policy':
                                value = value.replace("frame-ancestors 'none'", "frame-ancestors 'self'")
                            elif name == 'set-cookie':
                                cookie = SimpleCookie(); cookie.load(value)
                                for item in cookie.values():
                                    item['path'] = PREFIX + '/'
                                value = cookie.output(header='').strip()
                            elif name == 'location' and value.startswith('/'):
                                value = PREFIX + value
                            headers.append((name.encode('latin-1'), value.encode('latin-1')))
                        if scope['method'] == 'POST' and response.status == 200 and path in {'/api/login', '/api/logout'}:
                            if auto_cookie and self._login_cookie == auto_cookie:
                                self._login_cookie = ''
                            if path == '/api/logout':
                                # Explicit logout keeps this browser on the normal login page.
                                cookie = SimpleCookie({MANUAL_COOKIE: '1'})
                                cookie[MANUAL_COOKIE]['path'] = PREFIX + '/'
                                cookie[MANUAL_COOKIE]['httponly'] = True
                                cookie[MANUAL_COOKIE]['samesite'] = 'Strict'
                                cookie[MANUAL_COOKIE]['secure'] = upstream_headers['x-forwarded-proto'] == 'https'
                                headers.append((b'set-cookie', cookie.output(header='').strip().encode('latin-1')))
                        await send({'type': 'http.response.start', 'status': response.status, 'headers': headers})
                        async for chunk in response.content.iter_chunked(64 * 1024):
                            await send({'type': 'http.response.body', 'body': chunk, 'more_body': True})
                        await send({'type': 'http.response.body', 'body': b''})
        except (aiohttp.ClientError, OSError, RuntimeError):
            # Do not include upstream headers, cookies or URLs in browser errors.
            if websocket:
                with contextlib.suppress(Exception):
                    await WebSocket(scope, receive, send).close(code=1011)
            else:
                raise

    async def proxy_socket(self, session, url, scope, receive, send, headers):
        client = WebSocket(scope, receive, send)
        async with session.ws_connect(url, headers=headers, max_msg_size=16 * 1024 * 1024) as upstream:
            await client.accept()
            async def incoming():
                try:
                    while True:
                        message = await client.receive()
                        if message['type'] == 'websocket.disconnect':
                            return
                        if message.get('bytes') is not None:
                            await upstream.send_bytes(message['bytes'])
                        elif message.get('text') is not None:
                            await upstream.send_str(message['text'])
                except WebSocketDisconnect:
                    pass
            async def outgoing():
                async for message in upstream:
                    if message.type == aiohttp.WSMsgType.BINARY:
                        await client.send_bytes(message.data)
                    elif message.type == aiohttp.WSMsgType.TEXT:
                        await client.send_text(message.data)
                    else:
                        break
            tasks = [asyncio.create_task(incoming()), asyncio.create_task(outgoing())]
            try:
                await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            finally:
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                with contextlib.suppress(Exception):
                    await client.close()
