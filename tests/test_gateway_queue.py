"""Tests for MessageQueue: worker loop, dead-letter, backpressure."""

import asyncio

import pytest

from python.helpers.channel_bridge import NormalizedMessage
from python.helpers.message_queue import MessageQueue


def _make_msg(msg_id: str = "q1") -> NormalizedMessage:
    return NormalizedMessage(id=msg_id, channel="test", text="hi")


@pytest.mark.unit
class TestMessageQueue:
    def test_set_handler_and_process(self):
        async def run():
            q = MessageQueue(max_size=10, max_retries=1, retry_delay=0.01)
            results = []

            async def handler(msg):
                results.append(msg.id)
                return "ok"

            q.set_handler(handler)
            await q.start()
            await q.enqueue(_make_msg("m1"))
            # Give worker time to process
            await asyncio.sleep(0.2)
            await q.stop()
            assert results == ["m1"]

        asyncio.run(run())

    def test_dead_letter_on_failure(self):
        async def run():
            q = MessageQueue(max_size=10, max_retries=1, retry_delay=0.01)

            async def failing_handler(msg):
                raise RuntimeError("boom")

            q.set_handler(failing_handler)
            await q.start()
            await q.enqueue(_make_msg("fail1"))
            # Wait for retries and dead-letter
            await asyncio.sleep(0.5)
            await q.stop()
            assert q.dead_letter_count >= 1
            dl = q.dead_letters
            assert any(e.message.id == "fail1" for e in dl)
            assert any(e.last_error == "boom" for e in dl)

        asyncio.run(run())

    def test_no_handler_dead_letters(self):
        async def run():
            q = MessageQueue(max_size=10, max_retries=1, retry_delay=0.01)
            # No handler set
            await q.start()
            await q.enqueue(_make_msg("no_handler"))
            await asyncio.sleep(0.3)
            await q.stop()
            assert q.dead_letter_count >= 1

        asyncio.run(run())

    def test_stats(self):
        async def run():
            q = MessageQueue(max_size=50, max_retries=2)
            s = q.stats()
            assert s["pending"] == 0
            assert s["dead_letters"] == 0
            assert s["running"] is False
            assert s["max_size"] == 50
            assert s["max_retries"] == 2

        asyncio.run(run())

    def test_pending_count(self):
        async def run():
            q = MessageQueue(max_size=10, max_retries=1)
            # Enqueue without starting worker
            await q.enqueue(_make_msg("p1"))
            assert q.pending_count == 1

        asyncio.run(run())

    def test_start_idempotent(self):
        async def run():
            q = MessageQueue(max_size=10, max_retries=1, retry_delay=0.01)

            async def handler(msg):
                return "ok"

            q.set_handler(handler)
            await q.start()
            await q.start()  # second start should be no-op
            await q.stop()

        asyncio.run(run())

    def test_stop_without_start(self):
        async def run():
            q = MessageQueue()
            await q.stop()  # should not raise

        asyncio.run(run())
