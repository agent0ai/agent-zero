"""Real subprocess pipes cover multiplexing and cancellation without a browser SDK."""
import asyncio
import json
from pathlib import Path
import sys
from unittest.mock import AsyncMock
import pytest
from plugins._browser.helpers import sandbox


@pytest.mark.asyncio
async def test_real_pipe_concurrency_cleanup_ack_and_frame_backpressure(tmp_path):
    script = tmp_path / 'fixture.py'
    script.write_text('''
import asyncio, contextvars, runpy, sys, types
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]).resolve().parents[3]))
class Core:
    def __init__(self, *args, **kwargs):
        self.request_context_id = contextvars.ContextVar('context')
        self.request_options = contextvars.ContextVar('options')
        self.request_uploads = contextvars.ContextVar('uploads')
        self.interactive_view = types.SimpleNamespace(close=lambda: None)
        self.cleaned = False
    async def echo(self):
        return [self.request_context_id.get(), self.cleaned]
    async def slow(self):
        try:
            await asyncio.sleep(60)
        finally:
            await asyncio.sleep(.03)
            self.cleaned = True
    async def attach_screencast_consumer(self, stream, consume, stopped):
        await consume({'pixels': 'fixture'})
        return 'frame acknowledged'
    async def close(self): pass
sys.modules['plugins._browser.sandbox.runtime'] = types.SimpleNamespace(_BrowserRuntimeCore=Core)
sys.modules['plugins._browser.sandbox.display'] = types.SimpleNamespace()
runpy.run_path(sys.argv[1], run_name='__main__')
''')
    process = await asyncio.create_subprocess_exec(sys.executable, str(script),
        str(Path(sandbox.__file__).parents[1] / 'sandbox/rpc.py'),
        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE)
    async def send(value):
        process.stdin.write(json.dumps(value).encode() + b'\n')
        await process.stdin.drain()
    async def receive():
        return json.loads(await asyncio.wait_for(process.stdout.readline(), 3))
    async def request(id, method, **kwargs):
        await send({'id': id, 'method': method, 'context_id': id, 'args': [], 'kwargs': kwargs})
    try:
        await request('init', 'init', keyboard={})
        assert (await receive())['result'] is True
        await request('slow', 'slow')
        await request('other', 'echo')
        assert await receive() == {'id': 'other', 'result': ['other', False]}
        await send({'cancel': 'slow'})
        assert await receive() == {'id': 'slow', 'cancelled': True}
        await request('after', 'echo')
        assert (await receive())['result'] == ['after', True]
        await send({'id': 'frame', 'method': 'attach_screencast_consumer', 'context_id': 'ctx', 'args': ['s'], 'kwargs': {}})
        frame = await receive()
        assert frame['frame'] == {'pixels': 'fixture'}
        await request('while-frame', 'echo')
        assert (await receive())['id'] == 'while-frame'
        await send({'frame_ack': frame['frame_id']})
        assert await receive() == {'id': 'frame', 'result': 'frame acknowledged'}
        process.stdin.close()
        assert await asyncio.wait_for(process.wait(), 3) == 0
    finally:
        if process.returncode is None:
            process.kill()
            await process.wait()


@pytest.mark.asyncio
@pytest.mark.parametrize('failure', [RuntimeError('fixture setup failure'), asyncio.CancelledError()])
async def test_setup_failure_cleans_owned_worker_before_retry(monkeypatch, tmp_path, failure):
    connection = sandbox.BrowserConnection('fixture')
    connection.profile = tmp_path / 'profile'
    connection.downloads = tmp_path / 'downloads'
    monkeypatch.setattr(sandbox.worker, 'aprepare', AsyncMock(side_effect=failure))
    cleanup = AsyncMock()
    monkeypatch.setattr(connection, 'close', cleanup)
    with pytest.raises(type(failure)):
        await connection.start('fixture')
    cleanup.assert_awaited_once()
