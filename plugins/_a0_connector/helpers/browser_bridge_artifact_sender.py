"""Bounded, exact-route Core-to-browser input transfer with correlated ACKs."""

from __future__ import annotations

import asyncio
import base64
from dataclasses import dataclass
import hashlib
import re
from typing import Callable

from plugins._a0_connector.helpers.browser_bridge_artifacts import (
    ArtifactBinding, ArtifactDescriptor, MAX_ARTIFACT_BYTES, MAX_CHUNK_BYTES,
)
from plugins._a0_connector.helpers.browser_bridge_artifact_controller import _ack_binding
from plugins._a0_connector.helpers.browser_bridge_context import BrowserBridgeContextRoute
from plugins._a0_connector.helpers.browser_bridge_transport import PRODUCTION_BROWSER_BRIDGE_TRANSPORT as PROFILE


class BrowserBridgeArtifactSendError(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(slots=True)
class _Pending:
    binding: ArtifactBinding
    expected: dict
    future: asyncio.Future


class BrowserBridgeArtifactSender:
    """Send only server-supplied bytes for a currently authorized input binding.

    This class accepts no path, guessed artifact reference, page authority, or
    caller-selected principal. Its injected application authorizer must include
    exact operation, current turn, site and upload-consent checks.
    """

    def __init__(self, *, manager, authorizer: Callable[[ArtifactBinding], bool],
                 frame_timeout: float = 8.0):
        if not callable(authorizer) or not callable(getattr(manager, "emit_to", None)):
            raise TypeError("input artifact dependencies unavailable")
        if not isinstance(frame_timeout, (int, float)) or isinstance(frame_timeout, bool) or not 0 < frame_timeout <= 10:
            raise ValueError("invalid input artifact timeout")
        self._manager = manager
        self._authorizer = authorizer
        self._frame_timeout = frame_timeout
        self._pending: dict[str, _Pending] = {}
        self._tasks: dict[str, tuple[ArtifactBinding, asyncio.Task, int]] = {}
        self._used_ids: set[str] = set()
        self._closed = False

    def _current(self, binding: ArtifactBinding) -> bool:
        try:
            return bool(
                not self._closed and isinstance(binding, ArtifactBinding)
                and binding.transport_profile is PROFILE
                and binding.direction == "input" and binding.purpose == "upload_file"
                and binding.principal.permits_inbound("connector_browser_artifact_ack", PROFILE.handler_id)
                and self._authorizer(binding) is True
            )
        except Exception:
            return False

    async def send(self, binding: ArtifactBinding, *, data: bytes,
                   mime_type: str) -> ArtifactDescriptor:
        if (
            not self._current(binding) or not isinstance(data, bytes)
            or not 0 < len(data) <= MAX_ARTIFACT_BYTES
            or not isinstance(mime_type, str)
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]{0,126}/[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]{0,126}", mime_type) is None
        ):
            raise BrowserBridgeArtifactSendError("INPUT_ARTIFACT_DENIED")
        if binding.artifact_id in self._used_ids or len(self._used_ids) >= 2048 or len(self._tasks) >= 16 or sum(item[2] for item in self._tasks.values()) + len(data) > 100 * 1024 * 1024:
            raise BrowserBridgeArtifactSendError("INPUT_ARTIFACT_CAPACITY")
        self._used_ids.add(binding.artifact_id)
        task = asyncio.create_task(self._send_owned(binding, data, mime_type))
        self._tasks[binding.artifact_id] = (binding, task, len(data))
        def settled(done):
            current = self._tasks.get(binding.artifact_id)
            if current is not None and current[1] is done:
                self._tasks.pop(binding.artifact_id, None)
            if not done.cancelled():
                done.exception()
        task.add_done_callback(settled)
        # Caller cancellation cannot duplicate or abandon a half-sent transfer.
        return await asyncio.shield(task)

    async def _send_owned(self, binding, data, mime_type):
        descriptor = ArtifactDescriptor(binding.artifact_id, mime_type, len(data),
                                        "sha256:" + hashlib.sha256(data).hexdigest(), "upload_file")
        try:
            async with asyncio.timeout(120):
                await self._frame(binding, "begin", {
                    "mime_type": mime_type, "byte_count": len(data), "sha256": descriptor.sha256,
                }, {"status": "accepted", "next_chunk_index": 0, "received_bytes": 0})
                offset, index = 0, 0
                while offset < len(data):
                    chunk = data[offset:offset + MAX_CHUNK_BYTES]
                    await self._frame(binding, "chunk", {
                        "chunk_index": index, "data_base64": base64.b64encode(chunk).decode("ascii"),
                    }, {"status": "accepted", "next_chunk_index": index + 1, "received_bytes": offset + len(chunk)})
                    offset += len(chunk)
                    index += 1
                await self._frame(binding, "end", {}, {"status": "complete", "descriptor": descriptor.as_dict()})
                return descriptor
        except asyncio.CancelledError:
            raise
        except TimeoutError:
            raise BrowserBridgeArtifactSendError("INPUT_ARTIFACT_OUTCOME_UNKNOWN") from None
        except BrowserBridgeArtifactSendError:
            raise
        except Exception:
            raise BrowserBridgeArtifactSendError("INPUT_ARTIFACT_OUTCOME_UNKNOWN") from None
        finally:
            self._pending.pop(binding.artifact_id, None)
            self._tasks.pop(binding.artifact_id, None)

    async def _frame(self, binding, phase, extra, expected):
        if not self._current(binding):
            raise BrowserBridgeArtifactSendError("INPUT_ARTIFACT_AUTHORITY_LOST")
        common = _ack_binding(binding, phase)
        future = asyncio.get_running_loop().create_future()
        pending = _Pending(binding, common | expected, future)
        self._pending[binding.artifact_id] = pending
        try:
            async with asyncio.timeout(self._frame_timeout):
                await self._manager.emit_to(
                    PROFILE.namespace, binding.connector_sid, "connector_browser_artifact_chunk",
                    common | extra, handler_id=PROFILE.handler_id,
                    correlation_id=binding.artifact_id, expected_principal=binding.principal,
                )
                await future
            if not self._current(binding):
                raise BrowserBridgeArtifactSendError("INPUT_ARTIFACT_AUTHORITY_LOST")
        finally:
            if self._pending.get(binding.artifact_id) is pending:
                self._pending.pop(binding.artifact_id, None)

    async def receive_ack(self, route: BrowserBridgeContextRoute, document: object) -> dict:
        if not isinstance(route, BrowserBridgeContextRoute) or not isinstance(document, dict):
            raise BrowserBridgeArtifactSendError("INVALID_INPUT_ARTIFACT_ACK")
        value = dict(document)
        value.pop("correlationId", None)
        artifact_id = value.get("artifact_id")
        pending = self._pending.get(artifact_id) if isinstance(artifact_id, str) else None
        if (
            pending is None or pending.future.done()
            or pending.binding.principal is not route.principal
            or pending.binding.connector_sid != route.connector_sid
            or pending.binding.load_generation_id != route.load_generation_id
            or route.transport_profile is not PROFILE
            or not self._current(pending.binding)
            or value != pending.expected
        ):
            raise BrowserBridgeArtifactSendError("INVALID_INPUT_ARTIFACT_ACK")
        pending.future.set_result(None)
        return {"contract_version": 1, "status": "accepted"}

    def retire(self, *, principal, connector_sid, load_generation_id) -> None:
        for binding, task, _size in tuple(self._tasks.values()):
            if binding.principal is principal and binding.connector_sid == connector_sid and binding.load_generation_id == load_generation_id:
                task.get_loop().call_soon_threadsafe(task.cancel)

    async def close(self) -> None:
        self._closed = True
        tasks = [item[1] for item in self._tasks.values()]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
