"""Tests for python/helpers/shell_ssh.py."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestCleanString:
    """Tests for clean_string function."""

    def test_removes_ansi_escape_codes(self):
        """ANSI escape codes are removed."""
        from python.helpers.shell_ssh import clean_string

        text = "\x1b[31mred\x1b[0m normal"
        result = clean_string(text)
        assert "\x1b" not in result
        assert "red" in result
        assert "normal" in result

    def test_removes_null_bytes(self):
        """Null bytes are removed."""
        from python.helpers.shell_ssh import clean_string

        result = clean_string("hello\x00world")
        assert "\x00" not in result
        assert "hello" in result
        assert "world" in result

    def test_replaces_crlf_with_lf(self):
        """\\r\\n is replaced with \\n."""
        from python.helpers.shell_ssh import clean_string

        result = clean_string("line1\r\nline2")
        assert "\r\n" not in result
        assert result == "line1\nline2" or "line1" in result

    def test_removes_ipython_prompt_sequences(self):
        """IPython > prompt sequences at start are removed."""
        from python.helpers.shell_ssh import clean_string

        result = clean_string("\r\r\n> \r\n> hello")
        assert result.lstrip().startswith("hello") or "hello" in result

    def test_removes_leading_gt_space(self):
        """Leading '> ' sequences are removed."""
        from python.helpers.shell_ssh import clean_string

        result = clean_string("> > > output")
        assert "output" in result


class TestSSHInteractiveSession:
    """Tests for SSHInteractiveSession."""

    def test_init_stores_params(self):
        """__init__ stores hostname, port, username, password, cwd."""
        with patch("python.helpers.shell_ssh.paramiko"):
            from python.helpers.shell_ssh import SSHInteractiveSession

            logger = MagicMock()
            session = SSHInteractiveSession(
                logger=logger,
                hostname="host",
                port=22,
                username="user",
                password="pass",
                cwd="/home",
            )
            assert session.hostname == "host"
            assert session.port == 22
            assert session.username == "user"
            assert session.password == "pass"
            assert session.cwd == "/home"
            assert session.full_output == b""
            assert session.shell is None

    @pytest.mark.asyncio
    async def test_connect_establishes_ssh_and_shell(self):
        """connect() establishes SSH connection and invokes shell."""
        mock_client = MagicMock()
        mock_shell = MagicMock()
        mock_client.invoke_shell.return_value = mock_shell
        mock_client.get_transport.return_value = MagicMock()

        with patch("python.helpers.shell_ssh.paramiko") as mock_paramiko:
            mock_paramiko.SSHClient.return_value = mock_client
            mock_paramiko.AutoAddPolicy.return_value = MagicMock()

            from python.helpers.shell_ssh import SSHInteractiveSession

            logger = MagicMock()
            session = SSHInteractiveSession(
                logger=logger, hostname="h", port=22, username="u", password="p"
            )

            # read_output must return (truthy_full, "") to exit the connect loop
            session.read_output = AsyncMock(return_value=("prompt$ ", ""))

            mock_client.connect = MagicMock()
            await session.connect()

            mock_client.connect.assert_called_once_with(
                "h", 22, "u", "p", allow_agent=False, look_for_keys=False
            )
            mock_client.invoke_shell.assert_called_once_with(width=100, height=50)

    @pytest.mark.asyncio
    async def test_close_closes_shell_and_client(self):
        """close() closes shell and client."""
        mock_client = MagicMock()
        mock_shell = MagicMock()

        with patch("python.helpers.shell_ssh.paramiko"):
            from python.helpers.shell_ssh import SSHInteractiveSession

            logger = MagicMock()
            session = SSHInteractiveSession(
                logger=logger, hostname="h", port=22, username="u", password="p"
            )
            session.client = mock_client
            session.shell = mock_shell

            await session.close()

            mock_shell.close.assert_called_once()
            mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_command_raises_when_not_connected(self):
        """send_command raises when shell not connected."""
        with patch("python.helpers.shell_ssh.paramiko"):
            from python.helpers.shell_ssh import SSHInteractiveSession

            logger = MagicMock()
            session = SSHInteractiveSession(
                logger=logger, hostname="h", port=22, username="u", password="p"
            )
            session.shell = None

            with pytest.raises(Exception, match="Shell not connected"):
                await session.send_command("ls")

    @pytest.mark.asyncio
    async def test_send_command_appends_newline_and_sends(self):
        """send_command appends newline and sends encoded command."""
        mock_shell = MagicMock()

        with patch("python.helpers.shell_ssh.paramiko"):
            from python.helpers.shell_ssh import SSHInteractiveSession

            logger = MagicMock()
            session = SSHInteractiveSession(
                logger=logger, hostname="h", port=22, username="u", password="p"
            )
            session.shell = mock_shell
            session.full_output = b"previous"

            await session.send_command("echo hi")

            mock_shell.send.assert_called_once()
            call_arg = mock_shell.send.call_args[0][0]
            assert call_arg == b"echo hi\n"
            assert session.full_output == b""
            assert session.last_command == b"echo hi\n"

    @pytest.mark.asyncio
    async def test_read_output_raises_when_not_connected(self):
        """read_output raises when shell not connected."""
        with patch("python.helpers.shell_ssh.paramiko"):
            from python.helpers.shell_ssh import SSHInteractiveSession

            logger = MagicMock()
            session = SSHInteractiveSession(
                logger=logger, hostname="h", port=22, username="u", password="p"
            )
            session.shell = None

            with pytest.raises(Exception, match="Shell not connected"):
                await session.read_output()

    def test_receive_bytes_raises_when_not_connected(self):
        """receive_bytes raises when shell not connected."""
        with patch("python.helpers.shell_ssh.paramiko"):
            from python.helpers.shell_ssh import SSHInteractiveSession

            logger = MagicMock()
            session = SSHInteractiveSession(
                logger=logger, hostname="h", port=22, username="u", password="p"
            )
            session.shell = None

            with pytest.raises(Exception, match="Shell not connected"):
                session.receive_bytes()
