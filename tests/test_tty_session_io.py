"""Real PTY regressions, isolated so a blocking syscall cannot hang pytest."""
import asyncio
import gc
import hashlib
import os
from pathlib import Path
import signal
import subprocess
import sys
from types import SimpleNamespace

import pytest

from plugins._code_execution.helpers.tty_session import TTYSession


async def _start(command):
    session = TTYSession(command)
    await session.start()
    print(f"child_pid={session._proc.pid}", flush=True)
    return session


async def _until(session, marker):
    output = ""
    while marker not in output:
        output += await session.read(timeout=0.1) or ""
    return output


async def stale_readiness():
    session = await _start("/bin/bash --noprofile --norc -i")
    try:
        await session.read_full_until_idle(0.05, 1)
        # Another callback/nested loop may already have consumed the ready bytes.
        callback = asyncio.get_running_loop()._selector.get_key(session._pty_master).data[0]
        callback._callback()
        await session.sendline("printf 'still-responsive\\n'")
        await asyncio.wait_for(_until(session, "still-responsive"), 2)
    finally:
        await session.close()


async def large_write():
    session = await _start("/bin/bash --noprofile --norc -i")
    try:
        await session.read_full_until_idle(0.05, 1)
        # Many short lines avoid the terminal's per-line input limit.
        payload = "0123456789abcdef\n" * 16000
        command = "{\nsha256sum <<'PAYLOAD'\n" + payload + "PAYLOAD\nprintf 'write-%s\\n' done\n}\n"
        heartbeats = []
        async def heartbeat():
            while True:
                heartbeats.append(1)
                await asyncio.sleep(0.001)
        pulse = asyncio.create_task(heartbeat())
        try:
            await asyncio.wait_for(session.send(command), 5)
            output = await asyncio.wait_for(_until(session, "write-done"), 5)
            assert hashlib.sha256(payload.encode()).hexdigest() in output, output[-500:]
            assert len(heartbeats) > 1
        finally:
            pulse.cancel()
            await asyncio.gather(pulse, return_exceptions=True)
    finally:
        await session.close()


async def cancel_write():
    session = await _start("stty raw -echo; printf ready; sleep 30")
    try:
        await asyncio.wait_for(_until(session, "ready"), 2)
        pending = asyncio.create_task(session.send(b"x" * 1000000))
        await asyncio.sleep(0.05)
        assert not pending.done(), "Expected PTY backpressure"
        pending.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(pending, 1)
        assert session._pty_master_ref is None or session._pty_master_ref['fd'] is None
        await asyncio.wait_for(session.close(), 5)
    finally:
        session.kill()
        await session.close()


async def cancel_completed_write():
    session = await _start("/bin/bash --noprofile --norc -i")
    write = os.write
    try:
        await session.read_full_until_idle(0.05, 1)
        await session.sendline("{ export KEEP_STATE=preserved; printf 'setup-%s\\n' done; }")
        await asyncio.wait_for(_until(session, "setup-done"), 2)

        def cancel_after_write(fd, data):
            written = write(fd, data)
            if fd == session._pty_master:
                assert written == len(data)
                asyncio.get_running_loop().call_soon(asyncio.current_task().cancel)
            return written

        os.write = cancel_after_write
        try:
            pending = asyncio.create_task(session.sendline("printf 'sent-%s\\n' done"))
            with pytest.raises(asyncio.CancelledError):
                await pending
        finally:
            os.write = write

        assert session._pty_master_ref and session._pty_master_ref['fd'] is not None
        await session.sendline("printf 'kept=%s\\n' \"$KEEP_STATE\"")
        await asyncio.wait_for(_until(session, "kept=preserved"), 2)
    finally:
        os.write = write
        await session.close()


async def close_write(other_thread=False):
    session = await _start("stty raw -echo; printf ready; sleep 30")
    try:
        await asyncio.wait_for(_until(session, "ready"), 2)
        pending = asyncio.create_task(session.send(b"x" * 1000000))
        await asyncio.sleep(0.05)
        assert not pending.done()
        original_fd = session._pty_master
        if other_thread:
            await asyncio.to_thread(session.kill)
        else:
            session.kill()
        with pytest.raises(RuntimeError, match="closed"):
            await asyncio.wait_for(pending, 1)
        # Reusing a released fd must survive repeated session cleanup.
        fd = os.open(os.devnull, os.O_RDONLY)
        if fd != original_fd:
            os.dup2(fd, original_fd)
            os.close(fd)
            fd = original_fd
        try:
            session.kill()
            await session.close()
            os.fstat(fd)
        finally:
            os.close(fd)
    finally:
        await session.close()


async def close_from_thread():
    await close_write(other_thread=True)


async def destructor():
    session = await _start("/bin/bash --noprofile --norc -i")
    await session.close()
    loop = asyncio.get_running_loop()
    assert not getattr(loop, '_nest_patched', False)
    del session
    gc.collect()
    assert not getattr(loop, '_nest_patched', False), 'Destruction patched/reentered asyncio'


@pytest.mark.skipif(sys.platform != 'linux', reason='Linux PTY regression')
@pytest.mark.parametrize('case', ['stale_readiness', 'large_write', 'cancel_write', 'cancel_completed_write', 'close_write', 'close_from_thread', 'destructor'])
def test_tty_io_keeps_shared_loop_responsive(case):
    result = None
    try:
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), case],
            cwd=Path(__file__).resolve().parents[1],
            env={**os.environ, 'PYTHONPATH': str(Path(__file__).resolve().parents[1])},
            capture_output=True, text=True, timeout=15,
        )
        assert result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired as exc:
        result = exc
        pytest.fail(f'{case}: PTY blocked the event loop for 15 seconds')
    finally:
        output = getattr(result, 'stdout', '') or ''
        if isinstance(output, bytes):
            output = output.decode()
        for line in output.splitlines():
            if line.startswith('child_pid='):
                try:
                    os.killpg(int(line.split('=')[1]), signal.SIGKILL)
                except ProcessLookupError:
                    pass


@pytest.mark.parametrize('operation', ['close', 'resistant_close', 'kill', 'destructor'])
def test_windows_cleanup_without_posix_signals(monkeypatch, operation):
    from plugins._code_execution.helpers import tty_session

    calls = []

    class Child:
        pid = 123
        alive = True

        def isalive(self):
            return self.alive

        def read(self, size):
            raise EOFError

        def terminate(self):
            calls.append('terminate')
            if operation != 'resistant_close':
                self.alive = False

        def kill(self, sig):
            assert sig == 15
            calls.append('kill')
            self.alive = False

    child = Child()
    monkeypatch.setattr(tty_session, '_IS_WIN', True)
    monkeypatch.setattr(tty_session, 'signal', SimpleNamespace(SIGTERM=15))
    monkeypatch.setattr(tty_session, '_CLOSE_TIMEOUT_SECONDS', .01)
    monkeypatch.setattr(tty_session, 'winpty', SimpleNamespace(
        PtyProcess=SimpleNamespace(spawn=lambda *args, **kwargs: child)), raising=False)

    async def run():
        session = TTYSession('powershell.exe')
        await session.start()
        try:
            if operation in ('close', 'resistant_close'):
                await session.close()
            elif operation == 'kill':
                session.kill()
            else:
                session.__del__()
            assert not child.alive
            assert calls == (['terminate', 'kill'] if operation == 'resistant_close'
                             else ['terminate'] if operation == 'close' else ['kill'])
        finally:
            child.alive = False
            await session.close()

    asyncio.run(run())


if __name__ == '__main__':
    asyncio.run(globals()[sys.argv[1]]())
