from __future__ import annotations

import runpy
import sys
from types import ModuleType, SimpleNamespace

import pytest
from pathlib import Path

from plugins._searxng.helpers import searxng


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.asyncio
@pytest.mark.parametrize('state', ['idle', 'ready'])
async def test_search_prepares_worker_and_reports_cold_start(monkeypatch, state):
    events = []
    result = {'results': [], 'unresponsive_engines': [['google', 'CAPTCHA']]}
    async def prepare():
        events.append('prepare')
    async def call(payload, timeout):
        events.append((payload, timeout))
        return result
    monkeypatch.setattr(searxng, 'worker', SimpleNamespace(
        status=lambda: {'state': state}, aprepare=prepare, acall=call))
    progress = []
    assert await searxng.search('test query', progress=progress.append) is result
    assert events == ['prepare', ({'query': 'test query'}, 60)]
    assert progress == ([searxng.STARTUP_NOTICE] if state == 'idle' else []) + ['Searching the web']


@pytest.mark.asyncio
@pytest.mark.parametrize('query', ['', '  ', None, 42, 'x' * 8193])
async def test_invalid_query_does_not_start_worker(monkeypatch, query):
    monkeypatch.setattr(searxng, 'worker', None)
    with pytest.raises(ValueError, match='Search query'):
        await searxng.search(query)


@pytest.fixture
def guest_handler(monkeypatch):
    response = SimpleNamespace(status_code=200, get_json=lambda: {'results': []})
    calls = []
    class Client:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def post(self, path, data):
            calls.append((path, data))
            return response
    monkeypatch.setitem(sys.modules, 'searx', ModuleType('searx'))
    monkeypatch.setitem(sys.modules, 'searx.webapp', SimpleNamespace(app=SimpleNamespace(test_client=Client)))
    monkeypatch.setenv('SEARXNG_SETTINGS_PATH', '')
    monkeypatch.setenv('SEARXNG_SECRET', '')
    module = runpy.run_path(str(PROJECT_ROOT / 'plugins/_searxng/sandbox/worker.py'))
    return module['handle'], response, calls


def test_guest_calls_real_search_endpoint(guest_handler):
    handle, response, calls = guest_handler
    assert handle({'query': 'a query'}) == {'results': []}
    assert calls == [('/search', {'q': 'a query', 'format': 'json'})]


def test_guest_rejects_http_and_malformed_responses(guest_handler):
    handle, response, _ = guest_handler
    response.status_code = 503
    with pytest.raises(RuntimeError, match='HTTP 503'):
        handle({'query': 'test'})
    response.status_code = 200
    response.get_json = lambda: {'error': 'unexpected'}
    with pytest.raises(RuntimeError, match='invalid search response'):
        handle({'query': 'test'})


@pytest.mark.parametrize('query', ['', ' ', None, 123, 'x' * 8193])
def test_guest_rejects_invalid_queries(guest_handler, query):
    handle, _, calls = guest_handler
    with pytest.raises(ValueError, match='Search query'):
        handle({'query': query})
    assert calls == []


def test_hooks_install_lazily_and_remove_only_owned_sandbox(monkeypatch):
    from plugins._searxng import hooks
    import helpers.sandbox
    events = []
    monkeypatch.setattr(searxng, 'worker', SimpleNamespace(name='service-searxng', stop=lambda: events.append('stop')))
    monkeypatch.setattr(helpers.sandbox, 'get_manager', lambda: SimpleNamespace(
        delete=lambda name, **kwargs: events.append((name, kwargs))))
    assert hooks.install()['installed_on_demand'] is True
    assert events == []
    hooks.disable()
    hooks.uninstall()
    assert events == ['stop', 'stop', ('service-searxng', {'missing_ok': True})]


def test_searxng_assets_are_plugin_owned() -> None:
    expected = [
        "plugins/_searxng/plugin.yaml",
        "plugins/_searxng/hooks.py",
        "plugins/_searxng/sandbox/install.sh",
        "plugins/_searxng/sandbox/requirements.txt",
        "plugins/_searxng/sandbox/settings.yml",
        "plugins/_searxng/sandbox/worker.py",
        "plugins/_searxng/README.md",
        "plugins/_searxng/helpers/searxng.py",
        "plugins/_searxng/tools/search_engine.py",
        "plugins/_searxng/prompts/agent.system.tool.search_engine.md",
    ]
    removed_core = [
        "helpers/searxng.py",
        "helpers/searxng.py.dox.md",
        "tools/search_engine.py",
        "tools/search_engine.py.dox.md",
        "tools/knowledge_tool._py",
        "prompts/agent.system.tool.search_engine.md",
    ]

    for relative_path in expected:
        assert (PROJECT_ROOT / relative_path).is_file(), relative_path
    for relative_path in removed_core:
        assert not (PROJECT_ROOT / relative_path).exists(), relative_path


def test_outer_docker_images_have_no_searxng_runtime() -> None:
    removed_paths = [
        "docker/base/fs/ins/install_searxng.sh",
        "docker/base/fs/ins/install_searxng2.sh",
        "docker/base/fs/etc/searxng/settings.yml",
        "docker/base/fs/etc/searxng/limiter.toml",
        "docker/run/fs/exe/run_searxng.sh",
        "docker/run/fs/etc/searxng/settings.yml",
        "docker/run/fs/etc/searxng/limiter.toml",
    ]
    for relative_path in removed_paths:
        assert not (PROJECT_ROOT / relative_path).exists(), relative_path

    docker_files = [
        path
        for root in (
            PROJECT_ROOT / "docker" / "base",
            PROJECT_ROOT / "docker" / "run",
        )
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    ]
    docker_files.append(PROJECT_ROOT / "DockerfileLocal")
    combined = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore") for path in docker_files
    )

    forbidden = [
        "install_searxng",
        "run_searxng",
        "SEARXNG_SETTINGS_PATH",
        "/etc/searxng",
        "/usr/local/searxng",
        "searx-pyenv",
        "[program:run_searxng]",
    ]
    for marker in forbidden:
        assert marker not in combined, marker
