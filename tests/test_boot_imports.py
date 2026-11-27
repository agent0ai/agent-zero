"""Startup keeps preparation and unused protocol servers off the import path."""
import subprocess
import sys
from pathlib import Path

import pytest

from helpers import dotenv, runtime


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_prepare_does_not_import_model_stack():
    subprocess.run(
        [sys.executable, "-c", r"""
import importlib.abc
import runpy
import sys
import tempfile
from pathlib import Path

attempted = []
class RejectModels(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'models', 'litellm', 'onnxruntime'}:
            attempted.append(fullname)
            raise AssertionError(fullname)

sys.meta_path.insert(0, RejectModels())
from helpers import files, runtime
prepare = Path('prepare.py').resolve()
with tempfile.TemporaryDirectory() as root:
    files._base_dir = root
    Path(root, '.env').write_text('ROOT_PASSWORD=synthetic-root-secret\nAPI_KEY_TEST=synthetic-api-secret\n')
    Path(root, 'usr').mkdir()
    Path(root, 'usr/secrets.env').write_text('TOKEN=synthetic-global-secret\n')
    commands = []
    runtime.subprocess.run = lambda *args, **kwargs: commands.append((args, kwargs))
    sys.argv = ['prepare.py', '--dockerized=true']
    runpy.run_path(str(prepare), run_name='__main__')
    assert len(commands) == 1 and commands[0][1]['input'] == b'root:synthetic-root-secret'
    from helpers.print_style import PrintStyle
    printer = PrintStyle()
    text = printer.get('synthetic-root-secret synthetic-api-secret synthetic-global-secret')[0]
    assert 'synthetic-' not in text
    assert attempted == [], attempted
    assert 'models' not in sys.modules
    from helpers import secrets
    from types import SimpleNamespace
    secrets.get_secrets_manager = lambda: SimpleNamespace(mask_values=lambda text: 'context-masked')
    sys.modules['agent'] = SimpleNamespace()
    assert printer.get('later context')[0] == 'context-masked'
"""],
        cwd=PROJECT_ROOT,
        check=True,
        timeout=60,
    )


def test_root_password_requires_docker_and_persists_only_after_success(monkeypatch):
    writes = []
    monkeypatch.setattr(dotenv, "save_dotenv_value", lambda *args: writes.append(args))
    monkeypatch.setattr(runtime, "is_dockerized", lambda: False)
    with pytest.raises(Exception, match="only be set in dockerized"):
        runtime.set_root_password("test-password")

    monkeypatch.setattr(runtime, "is_dockerized", lambda: True)

    def failed(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "chpasswd")

    monkeypatch.setattr(runtime.subprocess, "run", failed)
    with pytest.raises(subprocess.CalledProcessError):
        runtime.set_root_password("test-password")
    assert writes == []

    def success(command, **kwargs):
        assert command == ["chpasswd"]
        assert kwargs == dict(input=b"root:test-password", capture_output=True, check=True)

    monkeypatch.setattr(runtime.subprocess, "run", success)
    runtime.set_root_password("test-password")
    assert writes == [(dotenv.KEY_ROOT_PASSWORD, "test-password")]
    from helpers.settings import set_root_password
    assert set_root_password is runtime.set_root_password


@pytest.mark.parametrize("desktop_routes", [False, True])
def test_protocol_imports_wait_for_request_and_preserve_access_checks(desktop_routes):
    subprocess.run(
        [sys.executable, "-c", r"""
import asyncio
from contextlib import nullcontext, asynccontextmanager
import importlib
import sys
import threading
from types import SimpleNamespace
import httpx
from helpers import settings
from helpers.ui_server import UiServerRuntime
if sys.argv[1] == 'desktop':
    from helpers.virtual_desktop_routes import install_route_hooks
    install_route_hooks()

config = settings.get_default_settings()
config.update(mcp_server_token='test-token', mcp_server_enabled=False, a2a_server_enabled=False)
settings.get_settings = lambda: config
events = []
@asynccontextmanager
async def monitor_lifespan(app):
    events.append('monitor start')
    yield
    events.append('monitor end')
@asynccontextmanager
async def socket_lifespan(*args):
    events.append('socket start')
    yield
    events.append('socket end')
from helpers import ui_server
ui_server.socket_lifespan = socket_lifespan
app = UiServerRuntime.create().build_asgi_app(SimpleNamespace(
    stage=lambda name: nullcontext(), lifespan=lambda: monitor_lifespan))
assert 'helpers.mcp_server' not in sys.modules
assert 'helpers.fasta2a_server' not in sys.modules
original_import = importlib.import_module
imports = []
def checked_import(name, *args, **kwargs):
    if name in {'helpers.mcp_server', 'helpers.fasta2a_server'}:
        assert threading.current_thread() is not threading.main_thread()
        imports.append(name)
    return original_import(name, *args, **kwargs)
importlib.import_module = checked_import

async def check():
    messages = [{'type': 'lifespan.startup'}, {'type': 'lifespan.shutdown'}]
    replies = []
    async def receive():
        return messages.pop(0)
    async def send(message):
        replies.append(message['type'])
    await app({'type': 'lifespan', 'asgi': {'version': '3.0'}}, receive, send)
    assert replies == ['lifespan.startup.complete', 'lifespan.shutdown.complete']
    assert events == ['monitor start', 'socket start', 'socket end', 'monitor end']
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
        # Concurrent cold requests share Python's import lock and the existing singleton.
        responses = await asyncio.gather(*(client.get('/mcp/t-wrong/http') for _ in range(2)))
        assert all(response.status_code == 403 for response in responses)
        from helpers.mcp_server import mcp_middleware
        from starlette.exceptions import HTTPException
        try:
            await mcp_middleware(None, None)
        except HTTPException as error:
            assert error.status_code == 403
        else:
            raise AssertionError('Disabled MCP server admitted a request')
        response = await client.get('/a2a/t-test-token/.well-known/agent-card.json')
        assert response.status_code == 403
        config.update(mcp_server_enabled=True, a2a_server_enabled=True)
        assert (await client.get('/mcp/t-wrong/http')).status_code == 403
        assert (await client.get('/a2a/t-wrong/.well-known/agent-card.json')).status_code == 401
    assert set(imports) == {'helpers.mcp_server', 'helpers.fasta2a_server'}
asyncio.run(check())
""", "desktop" if desktop_routes else "core"],
        cwd=PROJECT_ROOT,
        check=True,
        timeout=60,
    )
