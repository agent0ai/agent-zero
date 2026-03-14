import time

from agent import AgentContext
from python.api.message import Message
from python.helpers import perf_metrics
from python.helpers.defer import DeferredTask


class MessageAsync(Message):
    async def process(self, input: dict, request):
        started = time.perf_counter()
        status = "success"
        perf_metrics.increment("runtime.message_async.requests")
        try:
            return await super().process(input, request)
        except Exception:
            status = "error"
            perf_metrics.increment("runtime.message_async.errors")
            raise
        finally:
            perf_metrics.observe_ms(
                "runtime.message_async.duration_ms",
                (time.perf_counter() - started) * 1000.0,
                status=status,
            )

    async def respond(self, task: DeferredTask, context: AgentContext, timeout_seconds: int):
        return {
            "message": "Message received.",
            "context": context.id,
        }
