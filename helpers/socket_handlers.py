"""Explicit adapters for request-independent JSON administration operations."""

import asyncio
import importlib
import threading

from helpers.socket_api import SocketError, SocketHandler


async def _in_worker(operation):
    # Flask also runs request coroutines away from the ASGI transport loop.
    state = {}
    cancelled = threading.Event()

    async def run():
        state.update(loop=asyncio.get_running_loop(), task=asyncio.current_task())
        if cancelled.is_set():
            raise asyncio.CancelledError
        return await operation()

    try:
        return await asyncio.to_thread(lambda: asyncio.run(run()))
    except asyncio.CancelledError:
        cancelled.set()
        loop, task = state.get("loop"), state.get("task")
        if loop is not None:
            try:
                loop.call_soon_threadsafe(task.cancel)
            except RuntimeError:  # The worker may already have closed its loop.
                pass
        raise


def require_context(input: dict, field: str):
    from agent import AgentContext

    value = input.get(field)
    if not isinstance(value, str) or not value.strip():
        raise SocketError("INVALID_ARGUMENT", f"{field} must identify an existing chat")
    if AgentContext.get(value) is None:
        raise SocketError("NOT_FOUND", "Context not found")


def json_result(result) -> dict:
    from werkzeug.wrappers import Response

    if isinstance(result, Response):
        response = result
        try:
            if result.is_streamed:
                raise TypeError("Streaming HTTP responses need a dedicated socket handler")
            if not 200 <= result.status_code < 300:
                raise SocketError(f"HTTP_{result.status_code}", result.get_data(as_text=True))
            result = result.get_json()
        finally:
            response.close()
    if not isinstance(result, dict):
        raise TypeError("Expected a JSON object from the operation")
    explicit_success = result.get("ok") is True or result.get("success") is True
    if result.get("ok") is False or result.get("success") is False or (result.get("error") and not explicit_success):
        raise SocketError("OPERATION_FAILED", str(result.get("error") or "Operation failed"), details=result)
    return result


class JsonApiHandler(SocketHandler):
    """Subclass with a fixed module/class; callers cannot select arbitrary HTTP APIs."""

    api_module: str
    api_class: str
    context_field: str | None = None

    def validate(self, input: dict):
        if self.context_field:
            require_context(input, self.context_field)

    async def invoke(self, input: dict):
        module = importlib.import_module(self.api_module)
        handler = getattr(module, self.api_class)(self.app, self.thread_lock)
        return await handler.process(input, None)

    async def process(self, input: dict) -> dict:
        async def operation():
            self.validate(input)
            return json_result(await self.invoke(input))

        return await _in_worker(operation)
