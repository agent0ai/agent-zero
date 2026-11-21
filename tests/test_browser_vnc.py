"""Test the actual authenticated byte bridge, assets, and private display launch."""
import asyncio
import os
import re
import shutil
import subprocess
from pathlib import Path
import struct
import sys
from types import SimpleNamespace

from flask import Flask
from flask.sessions import SecureCookieSessionInterface
import httpx
import pytest
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from helpers import login, virtual_desktop
from plugins._browser.helpers import viewer_gateway as gateway
from plugins._browser.sandbox import display


@pytest.fixture
def anyio_backend():
    return 'asyncio'


@pytest.fixture
async def viewer(monkeypatch):
    connections = []
    async def echo(reader, writer):
        connections.append(True)
        try:
            writer.write(b'RFB 003.008\n')
            await writer.drain()
            while data := await reader.read(65536):
                writer.write(data)
                await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()
    server = await asyncio.start_server(echo, '127.0.0.1', 0)
    virtual_desktop.register_session(token='fixture', host='127.0.0.1', port=server.sockets[0].getsockname()[1],
                                    owner='browser-vnc', password='private')
    monkeypatch.setattr(gateway.plugins, 'get_toggle_state', lambda _: 'enabled')
    monkeypatch.setattr(login, 'get_credentials_hash', lambda: 'fixture-hash')
    flask = Flask(__name__)
    flask.secret_key = 'test-key'
    cookie = SecureCookieSessionInterface().get_signing_serializer(flask).dumps({'authentication':'fixture-hash'})
    app = Starlette(routes=[Mount('/browser/vnc', gateway.BrowserVncGateway(flask))])
    yield SimpleNamespace(app=app, cookie='session='+cookie, connections=connections)
    virtual_desktop.unregister_session('fixture')
    server.close()
    await server.wait_closed()


@pytest.mark.anyio
async def test_viewer_credentials_assets_auth_and_paths(viewer):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=viewer.app), base_url='http://a0.test') as client:
        path='/browser/vnc/session/fixture/'
        for headers in ({}, {'cookie':'session=forged'}, {'cookie':viewer.cookie,'origin':'http://evil.test'},
                        {'cookie':viewer.cookie,'origin':'http://['},
                        {'cookie':viewer.cookie,'sec-fetch-site':'same-site'}):
            assert (await client.get(path+'credentials', headers=headers)).status_code==403
        headers={'cookie':viewer.cookie,'origin':'http://a0.test'}
        response=await client.get(path+'credentials',headers=headers)
        assert response.json()=={'password':'private'}
        assert response.headers['cache-control']=='no-store'
        for name in ('index.html','vnc.js','clipboard.js','audio.js','vendor/novnc/core/rfb.js'):
            response=await client.get(path+name,headers=headers)
            assert response.status_code==200
            assert response.headers['x-frame-options']=='SAMEORIGIN'
        for name in ('unknown', 'vendor/novnc/%2e%2e/%2e%2e/browser-store.js'):
            assert (await client.get(path+name,headers=headers)).status_code==404
        assert (await client.get('/browser/vnc/session/unknown/credentials',headers=headers)).status_code==404
    assert not viewer.connections


@pytest.mark.anyio
async def test_vnc_bridge_auth_origin_binary_and_disconnect(viewer):
    def exercise():
        with TestClient(viewer.app, base_url='http://a0.test') as client:
            url='ws://a0.test/browser/vnc/session/fixture/ws'
            for headers in ({}, {'cookie':viewer.cookie}, {'cookie':viewer.cookie,'origin':'http://evil.test'}):
                with pytest.raises(WebSocketDisconnect):
                    with client.websocket_connect(url,headers=headers): pass
            with client.websocket_connect(url,headers={'cookie':viewer.cookie,'origin':'http://a0.test'}) as socket:
                assert socket.receive_bytes()==b'RFB 003.008\n'
                socket.send_bytes(b'\x00\xffINPUT')
                assert socket.receive_bytes()==b'\x00\xffINPUT'
                socket.send_text('not RFB')
                with pytest.raises(WebSocketDisconnect): socket.receive_bytes()
    await asyncio.to_thread(exercise)
    assert len(viewer.connections)==1


@pytest.mark.anyio
async def test_audio_auth_silent_gaps_and_capture_cleanup(viewer, monkeypatch, tmp_path):
    marker = tmp_path / 'stopped'
    script = tmp_path / 'capture.py'
    script.write_text('import sys\nfrom pathlib import Path\n'
                      'sys.stdout.buffer.write(bytes(3840) + b"\\x01\\x00\\xff\\xff" * 960)\n'
                      'sys.stdout.buffer.flush()\nsys.stdin.buffer.read()\n'
                      f'Path({str(marker)!r}).touch()\n')
    calls = []
    def command(name, argv):
        calls.append((name, argv))
        return [sys.executable, str(script)]
    worker = SimpleNamespace(name='fixture', _paths=lambda: (SimpleNamespace(process_command=command), None))
    monkeypatch.setitem(sys.modules, 'plugins._browser.helpers.sandbox', SimpleNamespace(worker=worker))

    def exercise():
        with TestClient(viewer.app, base_url='http://a0.test') as client:
            url = 'ws://a0.test/browser/vnc/session/fixture/audio'
            for headers in ({}, {'cookie': viewer.cookie}, {'cookie': viewer.cookie, 'origin': 'http://evil.test'}):
                with pytest.raises(WebSocketDisconnect):
                    with client.websocket_connect(url, headers=headers):
                        pass
            assert not calls
            with client.websocket_connect(url, headers={'cookie': viewer.cookie, 'origin': 'http://a0.test'}) as socket:
                packet = socket.receive_bytes()
                assert struct.unpack('<Q', packet[:8]) == (960,)
                assert packet[8:] == b'\x01\x00\xff\xff' * 960
                # Let the gateway finish capture teardown before TestClient cancels the session.
                socket.close()
                assert socket.receive()['type'] == 'websocket.close'
    await asyncio.to_thread(exercise)
    assert len(calls) == 1 and marker.exists()
    assert not viewer.connections


def test_xvnc_private_credentials_and_loopback(monkeypatch, tmp_path):
    view=display.BrowserInteractiveView('fixture')
    view.audio = SimpleNamespace(start=lambda: None, close=lambda: None)
    view.state_dir=tmp_path
    commands=[]
    process=SimpleNamespace(poll=lambda:None, terminate=lambda:None, wait=lambda **_:None)
    def popen(command, **kwargs):
        commands.append(command)
        os.write(kwargs['pass_fds'][0],b'77\n')
        return process
    monkeypatch.setattr(display,'collect_status',lambda:{'available':True})
    monkeypatch.setattr(display.subprocess,'Popen',popen)
    monkeypatch.setattr(display.subprocess,'run',lambda *args,**kwargs:None)
    monkeypatch.setattr(display.native_display,'current_display_size',lambda *args,**kwargs:(1024,768))
    monkeypatch.setattr(display.native_display,'resize_display',lambda **kwargs:{'ok':True})
    viewer=view.ensure_viewer()
    command=commands[0]
    assert command[0]=='tuxee-Xvnc'
    assert command[command.index('-interface')+1]=='127.0.0.1'
    assert command[command.index('-SecurityTypes')+1]=='VncAuth'
    assert '-ac' not in command and command[command.index('-nolisten')+1]=='tcp'
    assert '-auth' in command and viewer['password']
    assert Path(view.xauthority).stat().st_mode & 0o777 == 0o600
    assert b'MIT-MAGIC-COOKIE-1' in Path(view.xauthority).read_bytes()
    view.resize(800, 600)
    settings = Path(view.gtk_config) / 'glib-2.0/settings/keyfile'
    assert 'window-size = (800, 600)' in settings.read_text()
    assert 'window-position = (0, 0)' in settings.read_text()
    view.close()
    assert view.password=='' and view.port==0


def test_repeated_viewer_size_does_not_launch_x_clients_or_rewrite_settings(monkeypatch, tmp_path):
    view = display.BrowserInteractiveView('fixture')
    view.state_dir = tmp_path
    view.display = 77
    view._server = SimpleNamespace(poll=lambda: None)
    calls = []
    monkeypatch.setattr(view, '_fit_file_dialog', lambda: calls.append('settings'))
    def resize(**kwargs):
        calls.append((kwargs['width'], kwargs['height']))
        return {'ok': True, 'width': kwargs['width'], 'height': kwargs['height']}
    monkeypatch.setattr(display.native_display, 'resize_display', resize)
    assert view.resize(1024, 768)['resized'] is False
    assert calls == []
    assert view.resize(800, 600)['ok']
    assert calls == [(800, 600), 'settings']
    view.ensure_viewer(800, 600)
    view.resize(800, 600)
    assert calls == [(800, 600), 'settings']
    monkeypatch.setattr(display.native_display, 'resize_display', lambda **kw: {'ok': False})
    assert not view.resize(900, 700)['ok']
    assert (view.width, view.height) == (800, 600)


@pytest.mark.parametrize('source', [
    'prepared', 'on_path', 'fresh', 'fresh_retry', 'missing_font',
    'cache_amd64', 'cache_arm64', 'cache_and_path', 'ambiguous',
])
def test_guest_installer_reuses_or_provisions_chromium(tmp_path, source):
    script = Path('plugins/_browser/sandbox/install.sh').read_text()
    script = re.sub(r'(?<!\w)/(?:etc|opt|usr|app|var|worker|plugin|support)\b',
                    lambda match: str(tmp_path) + match[0], script)
    for directory in ['app/plugins', 'etc', 'usr/local/bin', 'usr/local/lib',
                      'opt/tuxee-guest-bin', 'opt/tuxee-guest-audio', 'opt/runtime/bin', 'worker', 'bin']:
        (tmp_path / directory).mkdir(parents=True, exist_ok=True)
    (tmp_path / 'etc/os-release').write_text('VERSION_CODENAME=trixie\n')
    (tmp_path / 'opt/tuxee-guest-bin/tuxee-Xvnc').touch(mode=0o755)
    (tmp_path / 'worker/progress.py').touch()
    bin_dir = tmp_path / 'bin'
    (tmp_path / 'plugin').symlink_to(Path('plugins/_browser').resolve(), target_is_directory=True)
    for name in ['mkdir', 'ln', 'rm', 'grep', 'install']:
        (bin_dir / name).symlink_to(shutil.which(name))
    (bin_dir / 'python').symlink_to(sys.executable)

    def program(path, body):
        path.write_text('#!/bin/sh\n' + body)
        path.chmod(0o755)

    browser = tmp_path / 'opt/runtime/bin/a0-chromium'
    cache = tmp_path / 'opt/browsers'
    platform_dir = 'chrome-linux' if source == 'cache_arm64' else 'chrome-linux64'
    cached = cache / 'chromium-1228' / platform_dir / 'chrome'
    cached.parent.mkdir(parents=True)
    program(cached, 'test "$1" = --version')
    if source != 'on_path' and not source.startswith('fresh'):
        (cached.parents[1] / 'INSTALLATION_COMPLETE').touch()
    if source == 'ambiguous':
        shutil.copytree(cached.parents[1], cache / 'chromium-1229')
    if source in ('prepared', 'missing_font'):
        program(browser, 'test "$1" = --version')
    if source in ('prepared', 'on_path', 'cache_and_path'):
        program(bin_dir / 'chromium', 'test "$1" = --version')
    program(bin_dir / 'dpkg-query', """
        case "$source $*" in
            fresh*|missing_font*fonts-unifont*) exit 1 ;;
        esac
        printf 'installed'
    """)
    program(bin_dir / 'apt-get', """
        echo "$*" >> "$commands"
        if [ "$1" = update ] && [ "$fail_update" = yes ]; then exit 100; fi
        case " $* " in *' chromium '*)
            mkdir -p "$guest/usr/share/X11/xkb" "$guest/usr/bin"
            : > "$guest/usr/bin/xkbcomp"
            ln -s "$new_chromium" "$bin_dir/chromium"
        ;; esac
    """)
    new_chromium = tmp_path / 'package-binary'
    program(new_chromium, 'test "$1" = --version')
    commands = tmp_path / 'apt-commands'
    commands.touch()
    command = ['/bin/sh', '-ec', script]
    env = {
        'PATH': str(bin_dir), 'source': source, 'commands': str(commands),
        'bin_dir': str(bin_dir), 'new_chromium': str(new_chromium), 'guest': str(tmp_path),
    }
    if source == 'fresh_retry':
        assert subprocess.run(command, env={**env, 'fail_update': 'yes'}).returncode == 100
        assert commands.read_text() == 'update\n'
        commands.write_text('')
    if source == 'ambiguous':
        result = subprocess.run(command, env=env, capture_output=True, text=True)
        assert result.returncode and 'Multiple installed Chromium builds' in result.stderr
        assert commands.read_text() == '' and not browser.exists()
        return
    subprocess.run(command, check=True, env=env)
    for brand in ('opt/chrome_for_testing', 'chromium'):
        policy = tmp_path / 'etc' / brand / 'policies/managed/agent-zero-browser.json'
        assert policy.read_bytes() == Path('plugins/_browser/sandbox/install-browser-policy.json').read_bytes()
    if source in ('prepared', 'on_path') or source.startswith('cache_'):
        assert commands.read_text() == ''
    else:
        update, install = commands.read_text().splitlines()
        assert update == 'update' and 'fonts-unifont' in install.split()
        assert ('chromium' in install.split()) is source.startswith('fresh')
    if source.startswith('fresh'):
        assert (tmp_path / 'opt/tuxee-gui/xkb').is_dir()
        assert (tmp_path / 'opt/tuxee-gui/bin/xkbcomp').is_file()
    if source in ('prepared', 'missing_font'):
        assert browser.is_file() and not browser.is_symlink()
    elif source.startswith('cache_'):
        assert browser.resolve() == cached.resolve()
    else:
        assert browser.resolve() == (bin_dir / 'chromium').resolve()


@pytest.mark.parametrize('build_fails', [False, True])
def test_guest_display_build_cleanup_preserves_previous_packages(tmp_path, build_fails):
    script = Path('plugins/_browser/sandbox/install.sh').read_text()
    helpers = script[script.index('apt_updated='):script.index('python /worker/progress.py viewer')]
    script = helpers + script[script.index('        previous_manual='):script.index('\n    fi\n    for tool in /opt/tuxee-gui')]
    script = script.replace('/support', str(tmp_path / 'support')).replace('/tmp/a0-gui', str(tmp_path / 'build'))
    script = script.replace('/opt/tuxee-gui', str(tmp_path / 'bundle'))
    binary = tmp_path / 'bin'
    binary.mkdir()
    log = tmp_path / 'commands'
    for name in ('apt-get', 'apt-mark', 'dpkg-query'):
        tool = binary / name
        tool.write_text(f'#!/bin/sh\necho "{name} $*" >> "{log}"\nif [ "$1" = showmanual ]; then echo "python3 ca-certificates"; fi\n')
        tool.chmod(0o755)
    support = tmp_path / 'support'
    support.mkdir()
    mounts = tmp_path / 'bundle'
    mounts.mkdir()
    (support / 'build-gui.sh').write_text(
        'exit 1\n' if build_fails else
        'mkdir -p "$1/usr/local/lib/tuxee-gui/bin"\ntouch "$1/usr/local/lib/tuxee-gui/bin/tuxee-Xvnc"\n'
    )
    (support / 'bundle-gui.sh').write_text('true\n')
    result = subprocess.run(['sh', '-ec', script], env={**os.environ, 'PATH': str(binary) + os.pathsep + os.environ['PATH']})
    calls = log.read_text().splitlines()
    if build_fails:
        assert result.returncode != 0
        assert not any('autoremove' in call for call in calls)
    else:
        assert result.returncode == 0
        assert (mounts / 'bin/tuxee-Xvnc').is_file()
        assert calls[-2:] == ['apt-mark manual python3 ca-certificates', 'apt-get autoremove --purge -y']
