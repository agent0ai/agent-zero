from __future__ import annotations

from dataclasses import replace
import hashlib
import os
from pathlib import Path
import stat

import pytest

from helpers.ws_principal import WsPrincipal
from plugins._a0_connector.helpers.browser_bridge_artifacts import (
    ARTIFACT_CHUNK_EVENT,
    MAX_ARTIFACT_BYTES,
    MAX_CHUNK_BYTES,
    ArtifactBinding,
    BrowserBridgeArtifactError,
    BrowserBridgeArtifactReceiver,
)


def _principal(*, bridge_id="bridge-1", key_generation=3):
    return WsPrincipal(
        principal_type="browser_bridge",
        principal_id=bridge_id,
        subject_id="single_user",
        scopes=frozenset({"bridge.connect", "browser.artifact"}),
        handler_path="plugins/_a0_connector/ws_connector",
        handler_id="ws_connector.WsConnector",
        inbound_events=frozenset({ARTIFACT_CHUNK_EVENT}),
        outbound_events=frozenset({ARTIFACT_CHUNK_EVENT}),
        key_generation=key_generation,
    )


def _binding(principal=None, **changes):
    principal = principal or _principal()
    values = {
        "principal": principal,
        "connector_sid": "sid-1",
        "load_generation_id": "load-generation-1",
        "bridge_id": principal.principal_id,
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


def _digest(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def _spool_files(parent: Path) -> list[Path]:
    return [entry for child in parent.iterdir() for entry in child.iterdir()]


def test_default_authorizer_denies_before_spool_creation(tmp_path):
    receiver = BrowserBridgeArtifactReceiver(spool_parent=tmp_path)
    try:
        with pytest.raises(BrowserBridgeArtifactError) as exc:
            receiver.begin(
                _binding(),
                byte_count=3,
                sha256=_digest(b"abc"),
                mime_type="image/png",
            )
        assert exc.value.code == "SCOPE_DENIED"
        assert receiver.active_count == 0
        assert receiver.reserved_bytes == 0
        assert _spool_files(tmp_path) == []
    finally:
        receiver.close()


def test_private_spool_verifies_and_is_consumed_once_without_path_descriptor(tmp_path):
    binding = _binding()
    payload = b"verified screenshot bytes"
    receiver = BrowserBridgeArtifactReceiver(
        spool_parent=tmp_path,
        authorizer=lambda candidate: candidate.principal is binding.principal,
    )
    root = next(tmp_path.iterdir())
    try:
        progress = receiver.begin(
            binding,
            byte_count=len(payload),
            sha256=_digest(payload),
            mime_type="image/png",
        )
        assert progress.status == "accepted"
        assert progress.next_chunk_index == 0
        assert stat.S_IMODE(os.lstat(root).st_mode) == 0o700
        spool = _spool_files(tmp_path)
        assert len(spool) == 1
        assert binding.artifact_id not in spool[0].name
        assert stat.S_IMODE(os.lstat(spool[0]).st_mode) == 0o600

        receiver.append(binding, chunk_index=0, data=payload[:9])
        progress = receiver.append(binding, chunk_index=1, data=payload[9:])
        assert progress.received_bytes == len(payload)
        assert progress.next_chunk_index == 2
        descriptor = receiver.complete(binding)
        assert descriptor.as_dict() == {
            "artifact_id": "artifact-1",
            "mime_type": "image/png",
            "byte_count": len(payload),
            "sha256": _digest(payload),
            "purpose": "screenshot",
        }
        assert not hasattr(descriptor, "path")
        assert str(root) not in repr(descriptor)

        consumed = receiver.consume(
            binding,
            lambda stream, received: (stream.read(), received.as_dict()),
        )
        assert consumed == (payload, descriptor.as_dict())
        assert receiver.active_count == 0
        assert receiver.reserved_bytes == 0
        assert _spool_files(tmp_path) == []
        with pytest.raises(BrowserBridgeArtifactError) as exc:
            receiver.consume(binding, lambda stream, _descriptor: stream.read())
        assert exc.value.code == "ARTIFACT_TERMINAL"
    finally:
        receiver.close()
    assert list(tmp_path.iterdir()) == []


def test_cross_binding_frames_reject_without_deleting_legitimate_transfer(tmp_path):
    binding = _binding()
    receiver = BrowserBridgeArtifactReceiver(
        spool_parent=tmp_path, authorizer=lambda _candidate: True
    )
    receiver.begin(
        binding, byte_count=3, sha256=_digest(b"abc"), mime_type="image/png"
    )
    clone = _principal()
    mutations = (
        replace(binding, principal=clone),
        replace(binding, connector_sid="sid-other"),
        replace(binding, load_generation_id="load-other"),
        replace(binding, bridge_id="bridge-other", principal=_principal(bridge_id="bridge-other")),
        replace(binding, context_id="context-other"),
        replace(binding, browser_session_id="session-other"),
        replace(binding, turn_id="turn-other"),
        replace(binding, action_id="action-other"),
        replace(binding, op_id="op-other"),
        replace(binding, purpose="download"),
        replace(binding, direction="input", purpose="upload_file"),
    )
    try:
        for candidate in mutations:
            with pytest.raises(BrowserBridgeArtifactError) as exc:
                receiver.append(candidate, chunk_index=0, data=b"abc")
            assert exc.value.code == "SCOPE_DENIED"
            assert exc.value.aborted is False
            assert receiver.active_count == 1
        receiver.append(binding, chunk_index=0, data=b"abc")
        assert receiver.complete(binding).byte_count == 3
    finally:
        receiver.close()


@pytest.mark.parametrize(
    ("failure", "code"),
    (
        (
            lambda receiver, binding: receiver.append(
                binding, chunk_index=1, data=b"abc"
            ),
            "CHUNK_OUT_OF_ORDER",
        ),
        (
            lambda receiver, binding: receiver.append(
                binding, chunk_index=0, data=b"x" * (MAX_CHUNK_BYTES + 1)
            ),
            "CHUNK_SIZE_INVALID",
        ),
        (
            lambda receiver, binding: receiver.append(
                binding, chunk_index=0, data=b"abcd"
            ),
            "ARTIFACT_SIZE_MISMATCH",
        ),
        (lambda receiver, binding: receiver.complete(binding), "ARTIFACT_INTEGRITY_MISMATCH"),
    ),
)
def test_order_size_and_integrity_failures_abort_and_delete(
    tmp_path, failure, code
):
    binding = _binding()
    receiver = BrowserBridgeArtifactReceiver(
        spool_parent=tmp_path, authorizer=lambda _candidate: True
    )
    receiver.begin(
        binding, byte_count=3, sha256=_digest(b"xyz"), mime_type="image/png"
    )
    try:
        with pytest.raises(BrowserBridgeArtifactError) as exc:
            failure(receiver, binding)
        assert exc.value.code == code
        assert exc.value.aborted is True
        assert receiver.active_count == 0
        assert receiver.reserved_bytes == 0
        assert _spool_files(tmp_path) == []
        with pytest.raises(BrowserBridgeArtifactError) as reused:
            receiver.begin(
                binding,
                byte_count=3,
                sha256=_digest(b"xyz"),
                mime_type="image/png",
            )
        assert reused.value.code == "ARTIFACT_ID_REUSED"
    finally:
        receiver.close()


def test_wrong_digest_aborts_only_at_terminal_verification(tmp_path):
    binding = _binding()
    receiver = BrowserBridgeArtifactReceiver(
        spool_parent=tmp_path, authorizer=lambda _candidate: True
    )
    receiver.begin(
        binding, byte_count=3, sha256=_digest(b"xyz"), mime_type="image/png"
    )
    receiver.append(binding, chunk_index=0, data=b"abc")
    try:
        with pytest.raises(BrowserBridgeArtifactError) as exc:
            receiver.complete(binding)
        assert exc.value.code == "ARTIFACT_INTEGRITY_MISMATCH"
        assert exc.value.aborted is True
        assert _spool_files(tmp_path) == []
    finally:
        receiver.close()


def test_short_write_and_on_disk_size_mismatch_abort(tmp_path):
    first = _binding(artifact_id="artifact-short-write")
    receiver = BrowserBridgeArtifactReceiver(
        spool_parent=tmp_path, authorizer=lambda _candidate: True
    )
    receiver.begin(
        first, byte_count=3, sha256=_digest(b"abc"), mime_type="image/png"
    )
    transfer = receiver._transfers[first.artifact_id]
    writer = transfer.writer
    assert writer is not None

    class ShortWriter:
        def write(self, data):
            writer.write(data[:-1])
            return len(data) - 1

        def close(self):
            writer.close()

    transfer.writer = ShortWriter()
    with pytest.raises(BrowserBridgeArtifactError) as exc:
        receiver.append(first, chunk_index=0, data=b"abc")
    assert (exc.value.code, exc.value.aborted) == ("SPOOL_UNAVAILABLE", True)
    assert receiver.active_count == 0

    second = _binding(artifact_id="artifact-truncated")
    receiver.begin(
        second, byte_count=3, sha256=_digest(b"abc"), mime_type="image/png"
    )
    receiver.append(second, chunk_index=0, data=b"abc")
    spool = _spool_files(tmp_path)
    assert len(spool) == 1
    os.truncate(spool[0], 2)
    try:
        with pytest.raises(BrowserBridgeArtifactError) as exc:
            receiver.complete(second)
        assert (exc.value.code, exc.value.aborted) == (
            "ARTIFACT_INTEGRITY_MISMATCH",
            True,
        )
        assert receiver.active_count == 0
        assert _spool_files(tmp_path) == []
    finally:
        receiver.close()


def test_declarations_and_process_spool_resources_are_hard_bounded(tmp_path):
    receiver = BrowserBridgeArtifactReceiver(
        spool_parent=tmp_path,
        authorizer=lambda _candidate: True,
        max_artifacts=1,
        max_total_spool_bytes=10,
    )
    first = _binding(artifact_id="artifact-first")
    second = _binding(artifact_id="artifact-second")
    try:
        receiver.begin(
            first, byte_count=8, sha256=_digest(b"12345678"), mime_type="image/png"
        )
        with pytest.raises(BrowserBridgeArtifactError) as exc:
            receiver.begin(
                second, byte_count=1, sha256=_digest(b"1"), mime_type="image/png"
            )
        assert exc.value.code == "ARTIFACT_REGISTRY_FULL"
        assert receiver.abort(first) is True

        with pytest.raises(BrowserBridgeArtifactError) as exc:
            receiver.begin(
                second, byte_count=11, sha256=_digest(b"x" * 11), mime_type="image/png"
            )
        assert exc.value.code == "ARTIFACT_SPOOL_FULL"
        with pytest.raises(BrowserBridgeArtifactError) as exc:
            receiver.begin(
                second,
                byte_count=MAX_ARTIFACT_BYTES + 1,
                sha256=_digest(b""),
                mime_type="image/png",
            )
        assert exc.value.code == "ARTIFACT_SIZE_INVALID"
        assert receiver.active_count == 0
    finally:
        receiver.close()


@pytest.mark.parametrize("operation", ("begin", "append", "complete", "consume"))
def test_current_route_authorization_is_rechecked_and_loss_purges_spool(
    tmp_path, operation
):
    allowed = [True]
    binding = _binding()
    payload = b"abc"
    receiver = BrowserBridgeArtifactReceiver(
        spool_parent=tmp_path, authorizer=lambda _candidate: allowed[0]
    )
    receiver.begin(
        binding,
        byte_count=len(payload),
        sha256=_digest(payload),
        mime_type="image/png",
    )
    if operation in {"complete", "consume"}:
        receiver.append(binding, chunk_index=0, data=payload)
    if operation == "consume":
        receiver.complete(binding)
    allowed[0] = False
    try:
        with pytest.raises(BrowserBridgeArtifactError) as exc:
            if operation == "begin":
                receiver.begin(
                    binding,
                    byte_count=len(payload),
                    sha256=_digest(payload),
                    mime_type="image/png",
                )
            elif operation == "append":
                receiver.append(binding, chunk_index=0, data=payload)
            elif operation == "complete":
                receiver.complete(binding)
            else:
                receiver.consume(binding, lambda stream, _descriptor: stream.read())
        assert exc.value.code == "SCOPE_DENIED"
        assert exc.value.aborted is True
        assert receiver.active_count == 0
        assert _spool_files(tmp_path) == []
    finally:
        receiver.close()


def test_expiry_disconnect_and_revocation_cleanup_are_exact(tmp_path):
    now = [1_000]
    principal = _principal()
    other_principal = _principal(bridge_id="bridge-2", key_generation=7)
    receiver = BrowserBridgeArtifactReceiver(
        spool_parent=tmp_path,
        authorizer=lambda _candidate: True,
        clock_ms=lambda: now[0],
        ttl_ms=50,
    )
    disconnected = _binding(principal, artifact_id="artifact-disconnect")
    revoked = _binding(
        other_principal,
        bridge_id="bridge-2",
        connector_sid="sid-2",
        artifact_id="artifact-revoke",
    )
    expiring = _binding(artifact_id="artifact-expire", op_id="op-expire")
    for binding in (disconnected, revoked, expiring):
        receiver.begin(
            binding, byte_count=1, sha256=_digest(b"x"), mime_type="image/png"
        )
    try:
        assert receiver.disconnect(
            principal=replace(principal),
            connector_sid="sid-1",
            load_generation_id="load-generation-1",
        ).artifacts == 0
        summary = receiver.disconnect(
            principal=principal,
            connector_sid="sid-1",
            load_generation_id="load-generation-1",
        )
        assert (summary.artifacts, summary.reserved_bytes) == (1, 1)
        assert receiver.revoke_bridge(
            bridge_id="bridge-2", key_generation=6
        ).artifacts == 0
        summary = receiver.revoke_bridge(bridge_id="bridge-2", key_generation=7)
        assert (summary.artifacts, summary.reserved_bytes) == (1, 1)
        assert receiver.active_count == 1

        later = _binding(artifact_id="artifact-later", op_id="op-later")
        receiver.begin(
            later, byte_count=1, sha256=_digest(b"x"), mime_type="image/png"
        )
        now[0] = 1_050
        summary = receiver.expire()
        assert (summary.artifacts, summary.reserved_bytes) == (2, 2)
        assert _spool_files(tmp_path) == []
    finally:
        receiver.close()


def test_consumer_failure_still_consumes_and_deletes_private_spool(tmp_path):
    binding = _binding()
    receiver = BrowserBridgeArtifactReceiver(
        spool_parent=tmp_path, authorizer=lambda _candidate: True
    )
    receiver.begin(
        binding, byte_count=3, sha256=_digest(b"abc"), mime_type="image/png"
    )
    receiver.append(binding, chunk_index=0, data=b"abc")
    receiver.complete(binding)

    def fail(_stream, _descriptor):
        raise RuntimeError("materializer failed")

    try:
        with pytest.raises(RuntimeError, match="materializer failed"):
            receiver.consume(binding, fail)
        assert receiver.active_count == 0
        assert _spool_files(tmp_path) == []
        with pytest.raises(BrowserBridgeArtifactError) as exc:
            receiver.consume(binding, fail)
        assert exc.value.code == "ARTIFACT_TERMINAL"
    finally:
        receiver.close()


def test_consume_reauthorizes_after_open_and_retains_quota_until_consumer_returns(
    tmp_path, monkeypatch
):
    allowed = [True]
    binding = _binding()
    payload = b"abc"
    receiver = BrowserBridgeArtifactReceiver(
        spool_parent=tmp_path,
        authorizer=lambda _candidate: allowed[0],
        max_artifacts=1,
    )
    receiver.begin(
        binding, byte_count=3, sha256=_digest(payload), mime_type="image/png"
    )
    receiver.append(binding, chunk_index=0, data=payload)
    receiver.complete(binding)

    def consume_while_bounded(stream, _descriptor):
        assert receiver.active_count == 1
        assert receiver.reserved_bytes == len(payload)
        with pytest.raises(BrowserBridgeArtifactError) as exc:
            receiver.begin(
                _binding(artifact_id="artifact-second"),
                byte_count=1,
                sha256=_digest(b"x"),
                mime_type="image/png",
            )
        assert exc.value.code == "ARTIFACT_REGISTRY_FULL"
        return stream.read()

    try:
        assert receiver.consume(binding, consume_while_bounded) == payload
        assert receiver.active_count == 0
        assert receiver.reserved_bytes == 0

        retry = _binding(artifact_id="artifact-post-open-revoke")
        receiver.begin(
            retry, byte_count=3, sha256=_digest(payload), mime_type="image/png"
        )
        receiver.append(retry, chunk_index=0, data=payload)
        receiver.complete(retry)
        real_open = os.open

        def revoke_after_open(path, flags):
            descriptor = real_open(path, flags)
            allowed[0] = False
            return descriptor

        monkeypatch.setattr(os, "open", revoke_after_open)
        called = []
        with pytest.raises(BrowserBridgeArtifactError) as exc:
            receiver.consume(
                retry,
                lambda stream, _descriptor: called.append(stream.read()),
            )
        assert (exc.value.code, exc.value.aborted) == ("SCOPE_DENIED", True)
        assert called == []
        assert receiver.active_count == 0
        assert receiver.reserved_bytes == 0
        assert _spool_files(tmp_path) == []
    finally:
        receiver.close()


def test_input_direction_is_exact_and_parent_symlinks_are_rejected(tmp_path):
    principal = _principal()
    input_binding = _binding(
        principal,
        direction="input",
        purpose="upload_file",
        artifact_id="artifact-upload",
    )
    receiver = BrowserBridgeArtifactReceiver(
        spool_parent=tmp_path, authorizer=lambda candidate: candidate == input_binding
    )
    try:
        receiver.begin(
            input_binding,
            byte_count=0,
            sha256=_digest(b""),
            mime_type="application/octet-stream",
        )
        assert receiver.complete(input_binding).purpose == "upload_file"
    finally:
        receiver.close()

    symlink = tmp_path / "spool-link"
    symlink.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match="non-symlink"):
        BrowserBridgeArtifactReceiver(spool_parent=symlink)

    with pytest.raises(BrowserBridgeArtifactError) as exc:
        replace(input_binding, direction="output")
    assert exc.value.code == "INVALID_PURPOSE"
