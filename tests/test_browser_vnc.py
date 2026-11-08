"""Test the actual authenticated byte bridge, assets, and private display launch."""
import asyncio
import os
from pathlib import Path
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
        for name in ('index.html','vnc.js','vendor/novnc/core/rfb.js'):
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


def test_xvnc_private_credentials_and_loopback(monkeypatch, tmp_path):
    view=display.BrowserInteractiveView('fixture')
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


def test_native_dependencies_keep_dialogs_fonts_and_handle_t64():
    from plugins._browser.sandbox.install_deps import native_packages, legacy_packages
    packages = native_packages('Package: libasound2t64\nPackage: libgtk-3-0t64\n')
    assert {'libasound2t64', 'libgtk-3-0t64', 'libx11-xcb1', 'dbus-x11', 'fonts-noto-color-emoji', 'fonts-wqy-zenhei'} <= set(packages)
    assert not {'libasound2', 'libgtk-3-0', 'xvfb', 'libllvm15', 'libgl1-mesa-dri'} & set(packages)
    assert {'libasound2', 'libgtk-3-0'} <= set(native_packages(''))
    assert legacy_packages('libllvm15:amd64 installed\nlibgl1-mesa-dri installed\nxpra-html5 installed\nxvfb config-files\nlibgtk-3-0 installed\nlibnss3 installed\nlibx11-xcb1 installed\n') == ['libllvm15:amd64', 'libgl1-mesa-dri', 'xpra-html5']


def test_native_installer_marks_runtime_before_retiring_legacy_dependencies(monkeypatch):
    from plugins._browser.sandbox import install_deps
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        output = 'libllvm15 installed\nlibgtk-3-0 installed\n' if command[0] == 'dpkg-query' else ''
        return SimpleNamespace(stdout=output)
    monkeypatch.setattr(install_deps.subprocess, 'run', run)
    install_deps.install()
    install = next(i for i, command in enumerate(calls) if command[:2] == ['apt-get', 'install'])
    mark = calls.index(['apt-mark', 'auto', 'libllvm15'])
    assert install < mark < calls.index(['apt-get', 'autoremove', '--purge', '-y'])
    assert 'libgtk-3-0' in calls[install] and '--no-install-recommends' in calls[install]


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


def test_browser_bootstrap_reuses_image_python_and_preserves_matching_environment(tmp_path):
    import subprocess
    import sys
    script = Path('plugins/_browser/sandbox/install.sh').read_text().split('ln -sfn /support')[0]
    runtime = tmp_path / 'runtime'
    progress = tmp_path / 'progress.py'
    progress.write_text('pass')
    script = script.replace('/opt/runtime', str(runtime)).replace('/worker/progress.py', str(progress))
    script = script.replace('/usr/local/share/fonts', str(tmp_path / 'fonts'))
    binary = tmp_path / 'bin'
    binary.mkdir()
    (binary / 'python').symlink_to(sys.executable)
    env = {**os.environ, 'PATH': str(binary) + os.pathsep + os.environ['PATH']}
    subprocess.run(['sh', '-ec', script], env=env, check=True)
    assert (runtime / 'bin/python').resolve() == Path(sys.executable).resolve()
    sentinel = runtime / 'keep-installed-packages'
    sentinel.touch()
    subprocess.run(['sh', '-ec', script], env=env, check=True)
    assert sentinel.exists()
    (runtime / 'bin/python').unlink()
    (runtime / 'bin/python').symlink_to(tmp_path / 'retired-python')
    subprocess.run(['sh', '-ec', script], env=env, check=True)
    assert (runtime / 'bin/python').resolve() == Path(sys.executable).resolve()
    assert not sentinel.exists()


@pytest.mark.parametrize('build_fails', [False, True])
def test_guest_display_build_cleanup_preserves_previous_packages(tmp_path, build_fails):
    import subprocess
    script = Path('plugins/_browser/sandbox/install.sh').read_text()
    script = script[script.index('    previous_manual='):script.index('\nfi\nfor tool')]
    script = script.replace('/support', str(tmp_path / 'support')).replace('/tmp/a0-gui', str(tmp_path / 'build'))
    script = script.replace('/opt/tuxee-gui', str(tmp_path / 'bundle'))
    binary = tmp_path / 'bin'
    binary.mkdir()
    log = tmp_path / 'commands'
    for name in ('apt-get', 'apt-mark'):
        tool = binary / name
        tool.write_text(f'#!/bin/sh\necho "{name} $*" >> "{log}"\nif [ "$1" = showmanual ]; then echo "python3 ca-certificates"; fi\n')
        tool.chmod(0o755)
    support = tmp_path / 'support'
    support.mkdir()
    (support / 'build-gui.sh').write_text('exit 1\n' if build_fails else 'mkdir -p "$1/usr/local/lib/tuxee-gui"\n')
    (support / 'bundle-gui.sh').write_text('true\n')
    result = subprocess.run(['sh', '-ec', script], env={**os.environ, 'PATH': str(binary) + os.pathsep + os.environ['PATH']})
    calls = log.read_text().splitlines()
    if build_fails:
        assert result.returncode != 0
        assert not any('autoremove' in call for call in calls)
    else:
        assert result.returncode == 0
        assert (tmp_path / 'bundle').is_dir()
        assert calls[-2:] == ['apt-mark manual python3 ca-certificates', 'apt-get autoremove --purge -y']


@pytest.mark.parametrize('image_uses_managed_python', [False, True])
def test_retired_runtime_cleanup_preserves_custom_image_interpreter(tmp_path, image_uses_managed_python):
    import subprocess
    managed = tmp_path / 'managed-python'
    managed.mkdir()
    interpreter = managed / 'python'
    interpreter.touch()
    cache = tmp_path / 'cache'
    cache.mkdir()
    script = Path('plugins/_browser/sandbox/install.sh').read_text().split('case "$base_interpreter" in', 1)[1].split('rm -rf /var/lib/apt/lists', 1)[0]
    script = 'case "$base_interpreter" in' + script
    script = script.replace('/root/.local/share/uv/python', str(managed)).replace('/root/.cache/uv', str(cache))
    subprocess.run(['sh', '-ec', script], check=True,
                   env={**os.environ, 'base_interpreter': str(interpreter) if image_uses_managed_python else '/usr/local/bin/python'})
    assert interpreter.exists() is image_uses_managed_python
    assert not cache.exists()
