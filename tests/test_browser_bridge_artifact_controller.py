from __future__ import annotations
import asyncio
import base64
import hashlib
import pytest
import io
from dataclasses import replace
from helpers.ws_principal import WsPrincipal
from plugins._a0_connector.helpers.browser_bridge_artifact_controller import (
    ARTIFACT_ACK_EVENT,
    ARTIFACT_CHUNK_EVENT,
    RESTRICTED_HANDLER_ID,
    ArtifactBindingLookup,
    BrowserBridgeArtifactController,
    BrowserBridgeArtifactControllerDenied,
    BrowserBridgeArtifactControllerError,
)
from plugins._a0_connector.helpers.browser_bridge_artifacts import (
    MAX_CHUNK_BYTES,
    ArtifactBinding,
    BrowserBridgeArtifactReceiver,
    BrowserBridgeArtifactError,
)
from plugins._a0_connector.helpers.browser_bridge_context import BrowserBridgeContextRoute
from types import SimpleNamespace
from PIL import Image
from plugins._a0_connector.helpers.browser_bridge_operations import OperationBinding, BrokerCompletion
from plugins._browser.helpers.extension_artifacts import (
    ExtensionScreenshotMaterializer,
    ExtensionArtifactError,
)
from plugins._browser.helpers.extension_runtime import encode_extension_call, ExtensionBrowserError
from plugins._a0_connector.helpers.browser_bridge_artifact_sender import (
    BrowserBridgeArtifactSender,
    BrowserBridgeArtifactSendError,
)
from test_browser_bridge_runtime_foundation import _principal as _runtime_principal


class _Manager:
    def __init__(self) -> None:
        self.emissions = []

    async def emit_to(self, *args, **kwargs):
        self.emissions.append((args, kwargs))


def _principal(*, bridge_id: str = "bridge-1") -> WsPrincipal:
    return WsPrincipal(
        principal_type="browser_bridge",
        principal_id=bridge_id,
        subject_id="subject-1",
        scopes=frozenset({"bridge.connect", "browser.artifact"}),
        handler_path="plugins/_a0_connector/ws_connector",
        handler_id=RESTRICTED_HANDLER_ID,
        inbound_events=frozenset({ARTIFACT_CHUNK_EVENT}),
        outbound_events=frozenset({ARTIFACT_ACK_EVENT}),
        key_generation=4,
    )


def _route(principal: WsPrincipal | None = None, *, sid: str = "sid-1"):
    return BrowserBridgeContextRoute(
        principal=principal or _principal(),
        connector_sid=sid,
        load_generation_id="load-1",
    )


def _binding(route: BrowserBridgeContextRoute, **changes) -> ArtifactBinding:
    values = {
        "principal": route.principal,
        "connector_sid": route.connector_sid,
        "load_generation_id": route.load_generation_id,
        "bridge_id": route.principal.principal_id,
        "context_id": "context-1",
        "browser_session_id": "session-1",
        "turn_id": "turn-1",
        "action_id": "action-1",
        "op_id": "op-1",
        "artifact_id": "artifact-1",
        "direction": "output",
        "purpose": "screenshot",
    }
    values.update(changes)
    return ArtifactBinding(**values)


def _frame(binding: ArtifactBinding, phase: str, **fields):
    return {
        "contract_version": 1,
        "phase": phase,
        "bridge_id": binding.bridge_id,
        "load_generation_id": binding.load_generation_id,
        "context_id": binding.context_id,
        "browser_session_id": binding.browser_session_id,
        "turn_id": binding.turn_id,
        "action_id": binding.action_id,
        "op_id": binding.op_id,
        "artifact_id": binding.artifact_id,
        "direction": binding.direction,
        "purpose": binding.purpose,
        **fields,
    }


def _digest(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _resolver(binding: ArtifactBinding):
    def resolve(lookup: ArtifactBindingLookup):
        assert lookup.op_id == binding.op_id
        return binding

    return resolve


def test_output_transfer_emits_exact_progress_and_pathless_descriptor(tmp_path):
    async def run():
        route = _route()
        binding = _binding(route)
        payload = b"bounded screenshot"
        manager = _Manager()
        receiver = BrowserBridgeArtifactReceiver(
            spool_parent=tmp_path,
            authorizer=lambda candidate: candidate == binding,
        )
        controller = BrowserBridgeArtifactController(
            receiver=receiver,
            binding_resolver=_resolver(binding),
            manager=manager,
        )
        try:
            begin = await controller.receive(
                route,
                _frame(
                    binding,
                    "begin",
                    byte_count=len(payload),
                    sha256=_digest(payload),
                    mime_type="image/png",
                ),
            )
            chunk = await controller.receive(
                route,
                _frame(
                    binding,
                    "chunk",
                    chunk_index=0,
                    data_base64=base64.b64encode(payload).decode("ascii"),
                ),
            )
            end = await controller.receive(route, _frame(binding, "end"))

            common = {
                "contract_version": 1,
                "bridge_id": "bridge-1",
                "load_generation_id": "load-1",
                "context_id": "context-1",
                "browser_session_id": "session-1",
                "turn_id": "turn-1",
                "action_id": "action-1",
                "op_id": "op-1",
                "artifact_id": "artifact-1",
                "direction": "output",
                "purpose": "screenshot",
            }
            assert begin == {
                **common,
                "phase": "begin",
                "status": "accepted",
                "next_chunk_index": 0,
                "received_bytes": 0,
            }
            assert chunk == {
                **common,
                "phase": "chunk",
                "status": "accepted",
                "next_chunk_index": 1,
                "received_bytes": len(payload),
            }
            assert end == {
                **common,
                "phase": "end",
                "status": "complete",
                "descriptor": {
                    "artifact_id": "artifact-1",
                    "mime_type": "image/png",
                    "byte_count": len(payload),
                    "sha256": _digest(payload),
                    "purpose": "screenshot",
                },
            }
            assert "path" not in repr(end)
            assert len(manager.emissions) == 3
            for (namespace, sid, event, payload), kwargs in manager.emissions:
                assert (namespace, sid, event) == (
                    "/ws",
                    "sid-1",
                    ARTIFACT_ACK_EVENT,
                )
                assert payload["contract_version"] == 1
                assert kwargs["handler_id"] == RESTRICTED_HANDLER_ID
                assert kwargs["expected_principal"] is route.principal
        finally:
            await controller.close()

    asyncio.run(run())


def test_screenshot_materializes_only_exact_verified_image_once(tmp_path):
    artifact = _binding(_route())
    binding = OperationBinding(artifact.principal, artifact.connector_sid, artifact.load_generation_id,
                               artifact.context_id, artifact.browser_session_id, artifact.turn_id,
                               artifact.action_id, artifact.op_id)
    output = io.BytesIO()
    Image.new("RGB", (2, 2), (240, 240, 240)).save(output, format="JPEG", quality=62)
    payload = output.getvalue()
    receiver = BrowserBridgeArtifactReceiver(spool_parent=tmp_path, authorizer=lambda _: True)
    descriptor = {"artifact_id": artifact.artifact_id, "mime_type": "image/jpeg", "byte_count": len(payload),
                  "sha256": "sha256:" + hashlib.sha256(payload).hexdigest(), "purpose": "screenshot"}
    receiver.begin(artifact, byte_count=len(payload), sha256=descriptor["sha256"], mime_type="image/jpeg")
    receiver.append(artifact, chunk_index=0, data=payload)
    receiver.complete(artifact)
    lease = SimpleNamespace(lease_id="lease-1", origin="https://example.com")
    written = []

    def save(**kwargs):
        written.append(kwargs)
        return SimpleNamespace(path="/owned-chat/screenshot.jpg", a0_path="/a0/usr/chats/context/screenshot.jpg")

    materialize = ExtensionScreenshotMaterializer(receiver=receiver, lease_for=lambda *_: lease, current=lambda _: True, save_image=save)
    call = encode_extension_call("screenshot_file", ("tab-1",), {"quality": 62, "full_page": False, "path": ""})
    assert call.action == "screenshot" and call.args == {"format": "jpeg", "quality": 62}
    result = {"lease_id": "lease-1", "browser_id": "tab-1", "tab_handle": "tab-1", "artifact_id": artifact.artifact_id}
    with pytest.raises(ExtensionArtifactError):
        materialize(binding, call, BrokerCompletion(ok=True, result={**result, "path": "/peer/path"}, artifacts=(descriptor,)))
    response = materialize(binding, call, BrokerCompletion(ok=True, result=result, artifacts=(descriptor,)))
    assert response["chat_scoped"] is True and response["mime"] == "image/jpeg"
    assert written[0]["context_id"] == binding.context_id and written[0]["payload"] == payload
    assert "image" not in response and "artifact_id" not in response
    with pytest.raises(BrowserBridgeArtifactError):
        materialize(binding, call, BrokerCompletion(ok=True, result=result, artifacts=(descriptor,)))
    for options in ({"full_page": True}, {"path": "/tmp/chosen"}, {"quality": True}, {"quality": 96}):
        with pytest.raises(ExtensionBrowserError):
            encode_extension_call("screenshot_file", ("tab-1",), options)
    receiver.close()
    assert not list(tmp_path.iterdir())


def _input_binding():
    return ArtifactBinding(_runtime_principal(), "sid-A", "generation-A", "bridge-A", "context-A", "session-A", "turn-A", "action-A", "op-A", "artifact-A", "input", "upload_file")


def test_input_sender_orders_chunks_and_exact_digest_ack_without_reuse():
    async def scenario():
        binding = _input_binding()
        route = BrowserBridgeContextRoute(binding.principal, binding.connector_sid, binding.load_generation_id)
        frames = []
        descriptor = None
        received = 0
        async def emit(_namespace, sid, event, frame, **kwargs):
            nonlocal descriptor, received
            assert kwargs["expected_principal"] is binding.principal
            assert sid == binding.connector_sid and event == "connector_browser_artifact_chunk"
            frames.append(frame)
            common = {key: frame[key] for key in (
                "contract_version", "phase", "bridge_id", "load_generation_id", "context_id",
                "browser_session_id", "turn_id", "action_id", "op_id", "artifact_id", "direction", "purpose",
            )}
            if frame["phase"] == "begin":
                descriptor = {"artifact_id": binding.artifact_id, "purpose": "upload_file", **{key: frame[key] for key in ("mime_type", "byte_count", "sha256")}}
                ack = common | {"status": "accepted", "next_chunk_index": 0, "received_bytes": 0}
            elif frame["phase"] == "chunk":
                import base64
                received += len(base64.b64decode(frame["data_base64"]))
                ack = common | {"status": "accepted", "next_chunk_index": frame["chunk_index"] + 1, "received_bytes": received}
            else:
                ack = common | {"status": "complete", "descriptor": descriptor}
            await sender.receive_ack(route, ack)
        sender = BrowserBridgeArtifactSender(manager=SimpleNamespace(emit_to=emit), authorizer=lambda value: value is binding)
        result = await sender.send(binding, data=b"x" * (MAX_CHUNK_BYTES + 1), mime_type="text/plain")
        assert result.byte_count == MAX_CHUNK_BYTES + 1
        assert [frame["phase"] for frame in frames] == ["begin", "chunk", "chunk", "end"]
        with pytest.raises(BrowserBridgeArtifactSendError):
            await sender.send(binding, data=b"x", mime_type="text/plain")
        await sender.close()
    asyncio.run(scenario())


def test_input_sender_cross_route_ack_and_retirement_cannot_complete():
    async def scenario():
        binding = _input_binding()
        emitted = asyncio.Event()
        async def emit(*args, **kwargs):
            emitted.set()
        sender = BrowserBridgeArtifactSender(manager=SimpleNamespace(emit_to=emit), authorizer=lambda value: True)
        waiting = asyncio.create_task(sender.send(binding, data=b"private", mime_type="text/plain"))
        await emitted.wait()
        pending = sender._pending[binding.artifact_id]
        wrong = BrowserBridgeContextRoute(binding.principal, "sid-other", binding.load_generation_id)
        with pytest.raises(BrowserBridgeArtifactSendError):
            await sender.receive_ack(wrong, pending.expected)
        assert not pending.future.done()
        sender.retire(principal=binding.principal, connector_sid=binding.connector_sid, load_generation_id=binding.load_generation_id)
        with pytest.raises(asyncio.CancelledError):
            await waiting
        await sender.close()
        assert not sender._tasks
    asyncio.run(scenario())


def test_input_sender_denies_without_current_consent_before_emitting():
    async def scenario():
        async def emit(*args, **kwargs):
            raise AssertionError("denied transfer emitted bytes")
        sender = BrowserBridgeArtifactSender(manager=SimpleNamespace(emit_to=emit), authorizer=lambda value: False)
        with pytest.raises(BrowserBridgeArtifactSendError):
            await sender.send(_input_binding(), data=b"private", mime_type="text/plain")
    asyncio.run(scenario())


def test_frame_and_resolved_binding_are_exact_and_input_stays_disabled(tmp_path):
    async def run():
        route = _route()
        binding = _binding(route)
        receiver = BrowserBridgeArtifactReceiver(
            spool_parent=tmp_path, authorizer=lambda _candidate: True
        )
        manager = _Manager()
        controller = BrowserBridgeArtifactController(
            receiver=receiver,
            binding_resolver=lambda _lookup: replace(
                binding, browser_session_id="wrong-session"
            ),
            manager=manager,
        )
        try:
            with pytest.raises(BrowserBridgeArtifactControllerDenied) as error:
                await controller.receive(
                    route,
                    _frame(
                        binding,
                        "begin",
                        byte_count=0,
                        sha256=_digest(b""),
                        mime_type="image/png",
                    ),
                )
            assert error.value.code == "ARTIFACT_BINDING_UNAVAILABLE"
            assert receiver.active_count == 0
            assert manager.emissions == []

            input_frame = _frame(
                binding,
                "begin",
                byte_count=0,
                sha256=_digest(b""),
                mime_type="image/png",
            )
            input_frame.update(direction="input", purpose="upload_file")
            with pytest.raises(BrowserBridgeArtifactControllerDenied) as error:
                await controller.receive(route, input_frame)
            assert error.value.code == "ARTIFACT_DIRECTION_UNAVAILABLE"

            invalid = _frame(
                binding,
                "chunk",
                chunk_index=0,
                data_base64="YQ",  # Valid bytes, but non-canonical unpadded form.
            )
            with pytest.raises(BrowserBridgeArtifactControllerError) as error:
                await controller.receive(route, invalid)
            assert error.value.code == "INVALID_CHUNK_BASE64"

            oversized = _frame(
                binding,
                "chunk",
                chunk_index=0,
                data_base64=base64.b64encode(
                    b"x" * (MAX_CHUNK_BYTES + 1)
                ).decode("ascii"),
            )
            with pytest.raises(BrowserBridgeArtifactControllerError) as error:
                await controller.receive(route, oversized)
            assert error.value.code == "CHUNK_SIZE_INVALID"
            assert manager.emissions == []
        finally:
            await controller.close()

    asyncio.run(run())


def test_sender_abort_is_exact_and_idempotently_acknowledged(tmp_path):
    async def run():
        route = _route()
        binding = _binding(route)
        manager = _Manager()
        receiver = BrowserBridgeArtifactReceiver(
            spool_parent=tmp_path, authorizer=lambda candidate: candidate == binding
        )
        controller = BrowserBridgeArtifactController(
            receiver=receiver,
            binding_resolver=_resolver(binding),
            manager=manager,
        )
        try:
            await controller.receive(
                route,
                _frame(
                    binding,
                    "begin",
                    byte_count=1,
                    sha256=_digest(b"x"),
                    mime_type="image/png",
                ),
            )
            request = _frame(binding, "abort", reason_code="CANCELED")
            first = await controller.receive(route, request)
            second = await controller.receive(route, request)
            assert first == second
            assert first["phase"] == "abort"
            assert first["status"] == "aborted"
            assert first["reason_code"] == "CANCELED"
            assert receiver.active_count == 0
        finally:
            await controller.close()

    asyncio.run(run())


def test_receiver_failure_emits_typed_abort_and_does_not_guess_chunk_duplicate(
    tmp_path,
):
    async def run():
        route = _route()
        binding = _binding(route)
        manager = _Manager()
        receiver = BrowserBridgeArtifactReceiver(
            spool_parent=tmp_path, authorizer=lambda candidate: candidate == binding
        )
        controller = BrowserBridgeArtifactController(
            receiver=receiver,
            binding_resolver=_resolver(binding),
            manager=manager,
        )
        try:
            begin_frame = _frame(
                binding,
                "begin",
                byte_count=3,
                sha256=_digest(b"abc"),
                mime_type="image/png",
            )
            assert (
                await controller.receive(route, begin_frame)
            )["status"] == "accepted"
            assert (
                await controller.receive(route, begin_frame)
            )["status"] == "duplicate"

            aborted = await controller.receive(
                route,
                _frame(
                    binding,
                    "chunk",
                    chunk_index=1,
                    data_base64=base64.b64encode(b"abc").decode("ascii"),
                ),
            )
            assert aborted["status"] == "aborted"
            assert aborted["phase"] == "chunk"
            assert aborted["reason_code"] == "CHUNK_OUT_OF_ORDER"
            assert receiver.active_count == 0
            assert manager.emissions[-1][0][3] == aborted
        finally:
            await controller.close()

    asyncio.run(run())


def test_background_expiry_and_disconnect_clean_only_owned_route(tmp_path):
    async def run():
        now = [1_000]
        first_route = _route()
        second_route = _route(_principal(bridge_id="bridge-2"), sid="sid-2")
        first = _binding(first_route, artifact_id="artifact-1")
        second = _binding(
            second_route,
            bridge_id="bridge-2",
            connector_sid="sid-2",
            artifact_id="artifact-2",
            op_id="op-2",
        )
        bindings = {first.artifact_id: first, second.artifact_id: second}
        receiver = BrowserBridgeArtifactReceiver(
            spool_parent=tmp_path,
            authorizer=lambda candidate: candidate in bindings.values(),
            clock_ms=lambda: now[0],
            ttl_ms=20,
        )
        manager = _Manager()
        controller = BrowserBridgeArtifactController(
            receiver=receiver,
            binding_resolver=lambda lookup: bindings.get(lookup.artifact_id),
            manager=manager,
            expiry_interval_seconds=0.01,
        )
        begin_fields = {
            "byte_count": 1,
            "sha256": _digest(b"x"),
            "mime_type": "image/png",
        }
        try:
            await controller.receive(
                first_route, _frame(first, "begin", **begin_fields)
            )
            await controller.receive(
                second_route, _frame(second, "begin", **begin_fields)
            )
            assert receiver.active_count == 2
            assert controller.expiry_task_active is True

            summary = await controller.disconnect(
                principal=first_route.principal,
                connector_sid=first_route.connector_sid,
                load_generation_id=first_route.load_generation_id,
            )
            assert summary.artifacts == 1
            assert receiver.active_count == 1
            assert controller.expiry_task_active is True

            now[0] = 1_021
            for _ in range(20):
                if receiver.active_count == 0:
                    break
                await asyncio.sleep(0.01)
            assert receiver.active_count == 0
            assert controller.expiry_task_active is False
        finally:
            await controller.close()

    asyncio.run(run())
