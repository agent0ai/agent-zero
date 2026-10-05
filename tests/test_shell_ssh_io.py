"""Exercise Paramiko's real packet and flow-control behavior without a server."""

import asyncio
import threading
import time
from types import SimpleNamespace

import paramiko
import pytest

from plugins._code_execution.helpers.shell_ssh import SSHInteractiveSession


def make_session(window=2**21):
    received = bytearray()

    def receive(message):
        message = paramiko.Message(message.asbytes())
        if message.get_byte() == b"\x5e":  # SSH_MSG_CHANNEL_DATA
            message.get_int()
            received.extend(message.get_binary())

    channel = paramiko.Channel(0)
    channel.transport = SimpleNamespace(
        _send_user_message=receive, _sanitize_packet_size=lambda size: size
    )
    channel._set_remote_channel(0, window, 32768)
    session = object.__new__(SSHInteractiveSession)
    session.shell = channel
    session.client = SimpleNamespace(close=lambda: None)
    return session, received


def test_ssh_sends_complete_nested_heredoc_across_packets():
    command = "bash <<'OUTER'\ncat <<'INNER'\n" + "héllo 🐇\n" * 20000 + "INNER\nOUTER"

    async def run():
        session, received = make_session()
        try:
            await session.send_command(command)
            assert bytes(received) == (command + "\n").encode()
            assert not session.shell.closed
        finally:
            await session.close()

    asyncio.run(run())


def test_cancel_blocked_ssh_send_closes_channel_without_stalling_loop():
    async def run():
        session, received = make_session(window=8)
        # Also bound a regression that blocks the event loop in sendall().
        watchdog = threading.Timer(2, session.shell.close)
        watchdog.start()
        pending = asyncio.create_task(session.send_command("x" * 100000))
        started = time.monotonic()
        try:
            while not received and not pending.done():
                await asyncio.sleep(0.01)
            assert time.monotonic() - started < 1
            assert bytes(received) == b"x" * 8
            assert not pending.done()
            pending.cancel()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(pending, 1)
            assert session.shell.closed
        finally:
            await session.close()
            watchdog.cancel()
            await asyncio.gather(pending, return_exceptions=True)

    # Loop shutdown also waits for the cancelled send's worker to finish.
    asyncio.run(run())
