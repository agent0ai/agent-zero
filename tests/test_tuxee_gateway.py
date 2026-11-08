"""Exercise the real HTTP and WebSocket proxy against a loopback transport fixture."""
import asyncio
from types import SimpleNamespace
import aiohttp.web
from flask import Flask
from flask.sessions import SecureCookieSessionInterface
import httpx
import pytest
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from plugins._desktop.helpers import gateway
from helpers import login


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def proxy(monkeypatch):
    captured = []
    state = SimpleNamespace(handler=None)
    async def upstream(request):
        captured.append(dict(request.headers))
        if state.handler:
            response = await state.handler(request)
            if response is not None:
                return response
        if request.path == '/ws':
            socket = aiohttp.web.WebSocketResponse()
            await socket.prepare(request)
            await socket.send_bytes(b'GUI')
            async for message in socket:
                if message.type == aiohttp.WSMsgType.TEXT:
                    await socket.send_str(message.data.upper())
            return socket
        body = await request.read()
        return aiohttp.web.Response(body=b'upstream:' + body, headers={
            'Set-Cookie': 'tuxee_session_fixture=opaque; Path=/; HttpOnly; SameSite=Strict',
            'Content-Security-Policy': "default-src 'self'; frame-ancestors 'none'; script-src 'sha256-fixed'",
            'X-Frame-Options': 'DENY',
        })
    server = aiohttp.web.Application()
    server.router.add_route('*', '/{path:.*}', upstream)
    runner = aiohttp.web.AppRunner(server)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, '127.0.0.1', 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    monkeypatch.setattr(gateway.runtime, 'start', lambda: port)
    monkeypatch.setattr(gateway.framework_runtime, 'is_dockerized', lambda: False)
    monkeypatch.delenv('ROOT_PASSWORD', raising=False)
    monkeypatch.setattr(gateway.plugins, 'get_toggle_state', lambda _: 'enabled')
    monkeypatch.setattr(login, 'get_credentials_hash', lambda: 'fixture-auth-hash')
    flask = Flask(__name__)
    flask.secret_key = 'fixture-only'
    token = SecureCookieSessionInterface().get_signing_serializer(flask).dumps({'authentication': 'fixture-auth-hash'})
    app = Starlette(routes=[Mount('/desktop/tuxee', gateway.TuxeeGateway(flask))])
    state.app, state.captured, state.cookie = app, captured, f'session={token}'
    yield state
    await runner.cleanup()


@pytest.mark.anyio
async def test_proxy_auth_and_origin_gate_precedes_upstream(proxy):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=proxy.app), base_url='http://a0.test') as client:
        for headers in ({}, {'cookie': 'session=forged'}, {'cookie': proxy.cookie, 'origin': 'https://evil.test'},
                        {'cookie': proxy.cookie, 'sec-fetch-site': 'cross-site'},
                        {'cookie': proxy.cookie, 'sec-fetch-site': 'same-site'}):
            assert (await client.get('/desktop/tuxee/api/me', headers=headers)).status_code == 403
        assert (await client.post('/desktop/tuxee/api/login', headers={'cookie': proxy.cookie})).status_code == 403
    assert proxy.captured == []


@pytest.mark.anyio
async def test_proxy_preserves_tuxee_auth_csrf_streams_and_restricts_cookie_path(proxy):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=proxy.app), base_url='https://a0.test') as client:
        result = await client.post('/desktop/tuxee/api/upload?path=test', content=b'FILE', headers={
            'cookie': proxy.cookie + '; tuxee_session_fixture=opaque; unrelated=private',
            'origin': 'https://a0.test', 'x-tuxee-csrf': 'csrf-fixture', 'x-tuxee-client': 'web', 'x-tuxee-size': '4', 'x-internal-auth': 'forged',
            'x-forwarded-host': 'evil.test', 'x-forwarded-proto': 'http',
        })
    assert result.status_code == 200
    assert result.content == b'upstream:FILE'
    assert 'Path=/desktop/tuxee/' in result.headers['set-cookie']
    assert result.headers['x-frame-options'] == 'SAMEORIGIN'
    assert result.headers['content-security-policy'] == "default-src 'self'; frame-ancestors 'self'; script-src 'sha256-fixed'"
    sent = {key.lower(): value for key, value in proxy.captured[-1].items()}
    assert sent['x-tuxee-client'] == 'web'
    assert sent['x-tuxee-size'] == '4'
    assert sent['host'] == 'a0.test' and sent['origin'] == 'https://a0.test'
    assert sent['cookie'] == 'tuxee_session_fixture=opaque'
    assert sent['x-tuxee-csrf'] == 'csrf-fixture' and sent['x-forwarded-proto'] == 'https'
    assert 'x-internal-auth' not in sent and 'x-forwarded-host' not in sent


@pytest.mark.anyio
async def test_websocket_auth_and_bidirectional_binary_text(proxy):
    def exercise():
        with TestClient(proxy.app, base_url='http://a0.test') as client:
            for headers in ({}, {'cookie': proxy.cookie, 'origin': 'http://evil.test'}, {'cookie': proxy.cookie}):
                with pytest.raises(WebSocketDisconnect):
                    with client.websocket_connect('ws://a0.test/desktop/tuxee/ws', headers=headers):
                        pass
            with client.websocket_connect('ws://a0.test/desktop/tuxee/ws', headers={'cookie': proxy.cookie, 'origin': 'http://a0.test'}) as ws:
                assert ws.receive_bytes() == b'GUI'
                ws.send_text('terminal input')
                assert ws.receive_text() == 'TERMINAL INPUT'
    await asyncio.to_thread(exercise)
    assert len(proxy.captured) == 1


@pytest.fixture
async def auto_proxy(proxy, monkeypatch):
    monkeypatch.setattr(gateway.framework_runtime, 'is_dockerized', lambda: True)
    monkeypatch.setenv('ROOT_PASSWORD', 'fixture-root-password')
    proxy.logins, proxy.sessions = [], {}
    proxy.login_status, proxy.issue_cookie, proxy.now = 200, True, 100
    monkeypatch.setattr(gateway, 'time', SimpleNamespace(monotonic=lambda: proxy.now))

    async def authenticated(request):
        if request.path == '/api/login':
            credentials = await request.json()
            proxy.logins.append(credentials)
            if proxy.login_status != 200:
                return aiohttp.web.Response(status=proxy.login_status, headers={'Location': '/unexpected-redirect'})
            assert request.headers['X-Tuxee-Client'] == 'web'
            assert credentials in ({'username': 'root', 'password': 'fixture-root-password'},
                                   {'username': 'manual', 'password': 'manual-password'})
            token = f'login-{len(proxy.logins)}'
            proxy.sessions[token] = {'csrf': token + '-csrf', 'uid': 0 if credentials['username'] == 'root' else 1000}
            response = aiohttp.web.json_response(proxy.sessions[token])
            if proxy.issue_cookie:
                response.set_cookie('tuxee_session_fixture', token, httponly=True, samesite='Strict')
            return response
        token = request.cookies.get('tuxee_session_fixture')
        session = proxy.sessions.get(token)
        if request.path in {'/', '/index.html'}:
            return aiohttp.web.Response(text='desktop' if session else 'login')
        if request.path == '/api/connection':
            return aiohttp.web.json_response({'authenticated': bool(session), **(session or {})})
        if not session:
            return aiohttp.web.Response(status=401)
        if request.method == 'POST' and request.headers.get('X-Tuxee-CSRF') != session['csrf']:
            return aiohttp.web.Response(status=403)
        if request.path == '/api/me':
            return aiohttp.web.json_response(session)
        if request.path == '/api/logout':
            del proxy.sessions[token]
            response = aiohttp.web.json_response({'ok': True})
            response.del_cookie('tuxee_session_fixture')
            return response
        if request.path != '/ws':
            return aiohttp.web.Response(body=await request.read())
    proxy.handler = authenticated
    return proxy


@pytest.mark.anyio
async def test_auto_login_keeps_credentials_server_side_and_preserves_csrf(auto_proxy):
    headers = {'cookie': auto_proxy.cookie, 'origin': 'https://a0.test'}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=auto_proxy.app), base_url='https://a0.test') as client:
        pages = await asyncio.gather(*(client.get('/desktop/tuxee/', headers=headers) for _ in range(4)))
        assert all(page.text == 'desktop' and 'set-cookie' not in page.headers for page in pages)
        assert len(auto_proxy.logins) == 1
        state = (await client.get('/desktop/tuxee/api/me', headers=headers)).json()
        assert state['uid'] == 0
        assert (await client.post('/desktop/tuxee/api/upload', headers=headers, content=b'FILE')).status_code == 403
        result = await client.post('/desktop/tuxee/api/upload', content=b'FILE',
                                  headers={**headers, 'x-tuxee-csrf': state['csrf']})
        assert result.status_code == 200 and result.content == b'FILE'
        assert not client.cookies
    assert 'Cookie' not in auto_proxy.captured[0]
    assert auto_proxy.captured[-1]['Cookie'] == 'tuxee_session_fixture=login-1'


@pytest.mark.anyio
@pytest.mark.parametrize('dockerized,password', [(False, 'fixture-root-password'), (True, '')])
async def test_auto_login_requires_container_and_root_password(auto_proxy, monkeypatch, dockerized, password):
    monkeypatch.setattr(gateway.framework_runtime, 'is_dockerized', lambda: dockerized)
    monkeypatch.setenv('ROOT_PASSWORD', password)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=auto_proxy.app), base_url='https://a0.test') as client:
        result = await client.get('/desktop/tuxee/', headers={'cookie': auto_proxy.cookie})
    assert result.text == 'login' and not auto_proxy.logins


@pytest.mark.anyio
@pytest.mark.parametrize('status,issue_cookie', [(401, True), (500, True), (307, True), (200, False)])
async def test_failed_auto_login_falls_back_and_bounds_retries(auto_proxy, status, issue_cookie):
    auto_proxy.login_status, auto_proxy.issue_cookie = status, issue_cookie
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=auto_proxy.app), base_url='https://a0.test') as client:
        for _ in range(2):
            result = await client.get('/desktop/tuxee/', headers={'cookie': auto_proxy.cookie})
            assert result.status_code == 200 and result.text == 'login'
        assert len(auto_proxy.logins) == 1
        auto_proxy.login_status, auto_proxy.issue_cookie, auto_proxy.now = 200, True, 161
        assert (await client.get('/desktop/tuxee/', headers={'cookie': auto_proxy.cookie})).text == 'desktop'
        assert len(auto_proxy.logins) == 2


@pytest.mark.anyio
@pytest.mark.parametrize('error', [TimeoutError, aiohttp.ClientConnectionError])
async def test_auto_login_transport_failure_shows_normal_login(auto_proxy, monkeypatch, error):
    def failed_login(*args, **kwargs):
        raise error('fixture login failure')
    monkeypatch.setattr(aiohttp.ClientSession, 'post', failed_login)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=auto_proxy.app), base_url='https://a0.test') as client:
        result = await client.get('/desktop/tuxee/', headers={'cookie': auto_proxy.cookie})
    assert result.status_code == 200 and result.text == 'login'


@pytest.mark.anyio
async def test_auto_login_renews_revoked_session_on_page_reload(auto_proxy):
    headers = {'cookie': auto_proxy.cookie}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=auto_proxy.app), base_url='https://a0.test') as client:
        assert (await client.get('/desktop/tuxee/', headers=headers)).text == 'desktop'
        auto_proxy.sessions.clear()
        assert (await client.get('/desktop/tuxee/api/connection', headers=headers)).json()['authenticated'] is False
        assert (await client.get('/desktop/tuxee/', headers=headers)).text == 'desktop'
        assert len(auto_proxy.logins) == 2


@pytest.mark.anyio
async def test_auto_login_respects_existing_a0_access_policy(auto_proxy, monkeypatch):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=auto_proxy.app), base_url='https://a0.test') as client:
        for headers in ({}, {'cookie': auto_proxy.cookie, 'origin': 'https://evil.test'},
                        {'cookie': auto_proxy.cookie, 'sec-fetch-site': 'cross-site'}):
            assert (await client.get('/desktop/tuxee/', headers=headers)).status_code == 403
        assert not auto_proxy.captured
        monkeypatch.setattr(login, 'get_credentials_hash', lambda: None)
        assert (await client.get('/desktop/tuxee/')).text == 'desktop'


@pytest.mark.anyio
async def test_logout_allows_manual_login_without_automatic_relogin(auto_proxy):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=auto_proxy.app), base_url='https://a0.test',
                                cookies={'session': auto_proxy.cookie.partition('=')[2]},
                                headers={'origin': 'https://a0.test'}) as client:
        assert (await client.get('/desktop/tuxee/')).text == 'desktop'
        rejected = await client.post('/desktop/tuxee/api/logout')
        assert rejected.status_code == 403 and gateway.MANUAL_COOKIE not in client.cookies
        response = await client.post('/desktop/tuxee/api/logout', headers={'x-tuxee-csrf': 'login-1-csrf'})
        assert response.status_code == 200
        assert client.cookies[gateway.MANUAL_COOKIE] == '1'
        marker = next(cookie for cookie in response.headers.get_list('set-cookie') if gateway.MANUAL_COOKIE in cookie)
        assert all(flag in marker for flag in ('HttpOnly', 'SameSite=Strict', 'Secure', 'Path=/desktop/tuxee/'))
        assert (await client.get('/desktop/tuxee/')).text == 'login'
        assert len(auto_proxy.logins) == 1
        response = await client.post('/desktop/tuxee/api/login', headers={'x-tuxee-client': 'web'},
                                     json={'username': 'manual', 'password': 'manual-password'})
        assert response.status_code == 200
        assert (await client.get('/desktop/tuxee/api/me')).json()['uid'] == 1000
        assert gateway.MANUAL_COOKIE not in auto_proxy.captured[-1]['Cookie']


@pytest.mark.anyio
async def test_manual_cookie_takes_precedence_over_shared_auto_session(auto_proxy):
    auto_proxy.sessions['manual'] = {'uid': 1000, 'csrf': 'manual-csrf'}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=auto_proxy.app), base_url='https://a0.test') as client:
        assert (await client.get('/desktop/tuxee/', headers={'cookie': auto_proxy.cookie})).text == 'desktop'
        headers = {'cookie': auto_proxy.cookie + '; tuxee_session_fixture=manual'}
        assert (await client.get('/desktop/tuxee/', headers=headers)).text == 'desktop'
        assert (await client.get('/desktop/tuxee/api/me', headers=headers)).json()['uid'] == 1000
        assert len(auto_proxy.logins) == 1


@pytest.mark.anyio
async def test_auto_login_cookie_authenticates_websockets(auto_proxy):
    def exercise():
        with TestClient(auto_proxy.app, base_url='http://a0.test') as client:
            headers = {'cookie': auto_proxy.cookie, 'origin': 'http://a0.test'}
            assert client.get('/desktop/tuxee/', headers=headers).text == 'desktop'
            with client.websocket_connect('ws://a0.test/desktop/tuxee/ws', headers=headers) as ws:
                assert ws.receive_bytes() == b'GUI'
                ws.send_text('terminal input')
                assert ws.receive_text() == 'TERMINAL INPUT'
    await asyncio.to_thread(exercise)
    assert auto_proxy.captured[-1]['Cookie'] == 'tuxee_session_fixture=login-1'
