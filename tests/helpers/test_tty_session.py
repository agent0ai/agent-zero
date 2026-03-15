"""Tests for python/helpers/tty_session.py."""

import asyncio
import sys
import platform
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

_IS_WIN = platform.system() == "Windows"


class TestTTYSessionInit:
    """Tests for TTYSession initialization."""

    def test_init_with_string_cmd(self):
        """__init__ accepts string command."""
        with patch("python.helpers.tty_session.sys"):
            from python.helpers.tty_session import TTYSession

            session = TTYSession("/bin/bash")
            assert session.cmd == "/bin/bash"
            assert session._proc is None

    def test_init_with_list_cmd_joins_with_space(self):
        """__init__ with list joins cmd with space."""
        with patch("python.helpers.tty_session.sys"):
            from python.helpers.tty_session import TTYSession

            session = TTYSession(["python", "-c", "print(1)"])
            assert session.cmd == "python -c print(1)"

    def test_init_stores_cwd_env_encoding_echo(self):
        """__init__ stores cwd, env, encoding, echo."""
        with patch("python.helpers.tty_session.sys"):
            from python.helpers.tty_session import TTYSession

            env = {"FOO": "bar"}
            session = TTYSession("cmd", cwd="/tmp", env=env, encoding="utf-8", echo=True)
            assert session.cwd == "/tmp"
            assert session.env == env
            assert session.encoding == "utf-8"
            assert session.echo is True


class TestTTYSessionStart:
    """Tests for TTYSession.start."""

    @pytest.mark.asyncio
    async def test_start_creates_proc_and_pump_task(self):
        """start() spawns process and creates pump task."""
        mock_proc = MagicMock()
        mock_proc.stdout = MagicMock()
        mock_proc.stdout.read = AsyncMock(side_effect=[b"data", b""])

        with patch("python.helpers.tty_session.sys"):
            with patch("python.helpers.tty_session._spawn_posix_pty", AsyncMock(return_value=mock_proc)):
                with patch("python.helpers.tty_session._IS_WIN", False):
                    from python.helpers.tty_session import TTYSession

                    session = TTYSession("/bin/bash")
                    await session.start()

                    assert session._proc is not None
                    assert hasattr(session, "_pump_task")


class TestTTYSessionClose:
    """Tests for TTYSession.close."""

    @pytest.mark.asyncio
    async def test_close_cancels_pump_and_terminates(self):
        """close() cancels pump task and terminates process."""
        mock_proc = MagicMock()
        mock_proc.wait = AsyncMock(return_value=0)

        with patch("python.helpers.tty_session.sys"):
            from python.helpers.tty_session import TTYSession

            session = TTYSession("/bin/bash")
            session._proc = mock_proc
            session._pump_task = asyncio.create_task(asyncio.sleep(100))

            await session.close()

            mock_proc.terminate.assert_called_once()
            mock_proc.wait.assert_called_once()


class TestTTYSessionSend:
    """Tests for TTYSession.send and sendline."""

    @pytest.mark.asyncio
    async def test_send_raises_when_not_started(self):
        """send raises when not started."""
        with patch("python.helpers.tty_session.sys"):
            from python.helpers.tty_session import TTYSession

            session = TTYSession("/bin/bash")
            with pytest.raises(RuntimeError, match="TTYSpawn is not started"):
                await session.send("data")

    @pytest.mark.asyncio
    async def test_sendline_appends_newline(self):
        """sendline appends newline to data."""
        mock_stdin = MagicMock()
        mock_stdin.write = MagicMock()
        mock_stdin.drain = AsyncMock()

        mock_proc = MagicMock()
        mock_proc.stdin = mock_stdin

        with patch("python.helpers.tty_session.sys"):
            from python.helpers.tty_session import TTYSession

            session = TTYSession("/bin/bash")
            session._proc = mock_proc

            await session.sendline("echo hi")
            mock_stdin.write.assert_called_once_with(b"echo hi\n")
            mock_stdin.drain.assert_called_once()


class TestTTYSessionKill:
    """Tests for TTYSession.kill."""

    def test_kill_noop_when_proc_none(self):
        """kill does nothing when _proc is None."""
        with patch("python.helpers.tty_session.sys"):
            from python.helpers.tty_session import TTYSession

            session = TTYSession("/bin/bash")
            session._proc = None
            session.kill()
            # No exception

    def test_kill_calls_proc_kill_when_running(self):
        """kill calls proc.kill() when process is running."""
        mock_proc = MagicMock()
        mock_proc.returncode = None

        with patch("python.helpers.tty_session.sys"):
            from python.helpers.tty_session import TTYSession

            session = TTYSession("/bin/bash")
            session._proc = mock_proc
            session.kill()
            mock_proc.kill.assert_called_once()

    def test_kill_ignores_process_lookup_error(self):
        """kill ignores ProcessLookupError when process already gone."""
        mock_proc = MagicMock()
        mock_proc.returncode = None
        mock_proc.kill.side_effect = ProcessLookupError

        with patch("python.helpers.tty_session.sys"):
            from python.helpers.tty_session import TTYSession

            session = TTYSession("/bin/bash")
            session._proc = mock_proc
            session.kill()
            # No exception


class TestTTYSessionRead:
    """Tests for TTYSession.read."""

    @pytest.mark.asyncio
    async def test_read_returns_from_queue(self):
        """read returns data from queue."""
        with patch("python.helpers.tty_session.sys"):
            from python.helpers.tty_session import TTYSession

            session = TTYSession("/bin/bash")
            session._buf = asyncio.Queue()
            session._buf.put_nowait("chunk1")

            result = await session.read(timeout=1)
            assert result == "chunk1"

    @pytest.mark.asyncio
    async def test_read_returns_none_on_timeout(self):
        """read returns None on timeout."""
        with patch("python.helpers.tty_session.sys"):
            from python.helpers.tty_session import TTYSession

            session = TTYSession("/bin/bash")
            session._buf = asyncio.Queue()

            result = await session.read(timeout=0.01)
            assert result is None


class TestTTYSessionReadFullUntilIdle:
    """Tests for TTYSession.read_full_until_idle."""

    @pytest.mark.asyncio
    async def test_read_full_until_idle_joins_chunks(self):
        """read_full_until_idle joins chunks from read_chunks_until_idle."""
        async def mock_chunks(idle_timeout, total_timeout):
            yield "a"
            yield "b"

        with patch("python.helpers.tty_session.sys"):
            from python.helpers.tty_session import TTYSession

            session = TTYSession("/bin/bash")
            with patch.object(session, "read_chunks_until_idle", mock_chunks):
                result = await session.read_full_until_idle(0.1, 1.0)
                assert result == "ab"
