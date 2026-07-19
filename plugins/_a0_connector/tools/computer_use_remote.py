"""computer_use_remote tool — drive the CLI host machine through the connected frontend."""
from __future__ import annotations

import asyncio
from pathlib import Path
import uuid
from typing import Any

from helpers import files, history
from helpers.tool import Response, Tool
from helpers.ws import NAMESPACE
from helpers.ws_manager import ConnectionNotFoundError, get_shared_ws_manager

from plugins._a0_connector.helpers.ws_runtime import (
    clear_pending_computer_use_op,
    computer_use_metadata_for_sid,
    select_computer_use_target_sid,
    store_pending_computer_use_op,
)


COMPUTER_USE_OP_TIMEOUT = 180.0
COMPUTER_USE_OP_EVENT = "connector_computer_use_op"
COMPUTER_USE_CAPTURE_DIR = ("tmp", "_a0_connector", "computer_use", "captures")
CAPTURE_TOKENS_ESTIMATE = 1500
MAX_CAPTURE_ARTIFACT_SIZE_BYTES = 25 * 1024 * 1024
REARM_REQUIRED_DEFAULT_MESSAGE = (
    "Computer use is configured, but the installed desktop-control backend is not armed."
)
_AUTO_CAPTURE_ACTIONS = {
    "start_session",
    "move",
    "click",
    "scroll",
    "key",
    "type",
}
_SETTLE_DELAY_START_SESSION = 0.2
_SETTLE_DELAY_MOVE = 0.1
_SETTLE_DELAY_CLICK = 0.35
_SETTLE_DELAY_SCROLL = 0.35
_SETTLE_DELAY_KEY = 0.2
_SETTLE_DELAY_TYPE = 0.25
_SETTLE_DELAY_GLOBAL_FOCUS = 0.45
_SETTLE_DELAY_PLAIN_ENTER = 0.3
_SETTLE_DELAY_SUBMIT = 0.45
_FRESH_CAPTURE_TIMEOUT = 0.45
_SUPPORTED_ACTIONS = {
    "start_session",
    "status",
    "capture",
    "move",
    "click",
    "scroll",
    "key",
    "type",
    "stop_session",
}


class ComputerUseRemote(Tool):
    async def execute(self, **kwargs: Any) -> Response:
        action = str(self.args.get("action") or "").strip().lower()
        if action not in _SUPPORTED_ACTIONS:
            return Response(
                message=(
                    "action is required and must be one of: "
                    "start_session, status, capture, move, click, scroll, key, type, stop_session"
                ),
                break_loop=False,
            )

        context_id = self.agent.context.id
        sid = select_computer_use_target_sid(context_id)
        if not sid:
            return Response(
                message=(
                    "computer_use_remote: no connected CLI currently advertises enabled local "
                    "computer use. Enable it in the CLI and choose a trust mode first."
                ),
                break_loop=False,
            )

        metadata = computer_use_metadata_for_sid(sid) or {}
        if str(metadata.get("status", "") or "").strip().lower() == "rearm required":
            return Response(
                message=self._format_error(
                    {
                        "code": "COMPUTER_USE_REARM_REQUIRED",
                        "error": str(metadata.get("last_error", "") or "").strip()
                        or REARM_REQUIRED_DEFAULT_MESSAGE,
                    }
                ),
                break_loop=False,
            )

        try:
            payload = self._build_payload(op_id=str(uuid.uuid4()), context_id=context_id, action=action)
            result = await self._dispatch_payload(sid=sid, payload=payload)
            capture_note = await self._maybe_attach_latest_capture(
                action=action,
                sid=sid,
                context_id=context_id,
                result=result,
            )
            message = self._extract_result(action, result)
        except ValueError as exc:
            return Response(
                message=f"computer_use_remote: {exc}",
                break_loop=False,
            )
        except ConnectionNotFoundError:
            return Response(
                message=(
                    "computer_use_remote: the selected CLI disconnected before the request "
                    "could be delivered."
                ),
                break_loop=False,
            )
        except asyncio.TimeoutError:
            return Response(
                message=f"computer_use_remote: timed out waiting for action={action!r}",
                break_loop=False,
            )
        except Exception as exc:
            return Response(
                message=f"computer_use_remote: error sending action={action!r}: {exc}",
                break_loop=False,
            )

        if capture_note:
            message = f"{message} {capture_note}".strip()

        return Response(
            message=message,
            break_loop=False,
        )

    async def _dispatch_payload(self, *, sid: str, payload: dict[str, Any]) -> dict[str, Any]:
        op_id = str(payload.get("op_id") or "").strip()
        loop = asyncio.get_running_loop()
        future: asyncio.Future[dict[str, Any]] = loop.create_future()
        store_pending_computer_use_op(
            op_id,
            sid=sid,
            future=future,
            loop=loop,
            context_id=str(payload.get("context_id") or "").strip() or None,
        )

        try:
            await get_shared_ws_manager().emit_to(
                NAMESPACE,
                sid,
                COMPUTER_USE_OP_EVENT,
                payload,
                handler_id=f"{self.__class__.__module__}.{self.__class__.__name__}",
            )
            result = await asyncio.wait_for(future, timeout=COMPUTER_USE_OP_TIMEOUT)
        finally:
            clear_pending_computer_use_op(op_id)

        if isinstance(result, dict):
            return result
        raise RuntimeError(f"Unexpected response format from CLI: {result!r}")

    async def _maybe_attach_latest_capture(
        self,
        *,
        action: str,
        sid: str,
        context_id: str,
        result: dict[str, Any],
    ) -> str:
        if action not in _AUTO_CAPTURE_ACTIONS or not bool(result.get("ok")):
            return ""

        data = result.get("result")
        result_data = dict(data) if isinstance(data, dict) else {}
        session_id = str(result_data.get("session_id") or self.args.get("session_id") or "").strip()
        if not session_id:
            return ""

        settle_seconds = self._auto_capture_settle_seconds(action)
        if settle_seconds > 0:
            await asyncio.sleep(settle_seconds)

        capture_payload = {
            "op_id": str(uuid.uuid4()),
            "context_id": context_id,
            "action": "capture",
            "session_id": session_id,
            "fresh": True,
            "fresh_timeout_seconds": _FRESH_CAPTURE_TIMEOUT,
        }
        capture_result = await self._dispatch_payload(sid=sid, payload=capture_payload)
        if not bool(capture_result.get("ok")):
            return f"Automatic screen refresh failed: {self._format_error(capture_result)}"

        capture_data = capture_result.get("result")
        if not isinstance(capture_data, dict):
            return "Automatic screen refresh failed: missing capture payload."

        try:
            summary = self._record_capture(capture_data)
        except Exception as exc:
            return f"Automatic screen refresh failed: {exc}"
        return f"Latest screen attached: {summary}"

    def _auto_capture_settle_seconds(self, action: str) -> float:
        if action == "start_session":
            return _SETTLE_DELAY_START_SESSION
        if action == "move":
            return _SETTLE_DELAY_MOVE
        if action == "click":
            return _SETTLE_DELAY_CLICK
        if action == "scroll":
            return _SETTLE_DELAY_SCROLL
        if action == "type" and self._coerce_bool(self.args.get("submit")):
            return _SETTLE_DELAY_SUBMIT
        if action == "type":
            return _SETTLE_DELAY_TYPE
        if action != "key":
            return 0.0

        keyset = {key.lower() for key in self._requested_keys()}
        if "super" in keyset or ("alt" in keyset and "tab" in keyset):
            return _SETTLE_DELAY_GLOBAL_FOCUS
        if keyset == {"enter"}:
            return _SETTLE_DELAY_PLAIN_ENTER
        return _SETTLE_DELAY_KEY

    def _requested_keys(self) -> list[str]:
        keys_value = self.args.get("keys")
        if isinstance(keys_value, (list, tuple)):
            return [str(item).strip() for item in keys_value if str(item).strip()]
        raw = str(keys_value or self.args.get("key", "") or "").strip()
        if not raw:
            return []
        return [part.strip() for part in raw.split("+") if part.strip()]

    def _build_payload(self, *, op_id: str, context_id: str, action: str) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "op_id": op_id,
            "context_id": context_id,
            "action": action,
        }
        session_id = str(self.args.get("session_id", "") or "").strip()
        if session_id:
            payload["session_id"] = session_id

        if action == "move":
            payload["x"] = self.args.get("x")
            payload["y"] = self.args.get("y")
        elif action == "click":
            if "x" in self.args:
                payload["x"] = self.args.get("x")
            if "y" in self.args:
                payload["y"] = self.args.get("y")
            payload["button"] = self.args.get("button", "left")
            payload["count"] = self._coerce_int(self.args.get("count", 1), name="count")
        elif action == "scroll":
            payload["dx"] = self._coerce_int(self.args.get("dx", self.args.get("delta_x", 0)), name="dx")
            payload["dy"] = self._coerce_int(self.args.get("dy", self.args.get("delta_y", 0)), name="dy")
        elif action == "key":
            if "keys" in self.args:
                payload["keys"] = self.args.get("keys")
            elif "key" in self.args:
                payload["key"] = self.args.get("key")
        elif action == "type":
            payload["text"] = self.args.get("text", "")
            if self._coerce_bool(self.args.get("submit")):
                payload["submit"] = True

        return payload

    def _extract_result(self, action: str, result: Any) -> str:
        if not isinstance(result, dict):
            return f"Unexpected response format from CLI: {result!r}"

        ok = bool(result.get("ok"))
        data = result.get("result")

        if not ok:
            return self._format_error(result)

        if not isinstance(data, dict):
            data = {}

        if action == "capture":
            summary = self._record_capture(data)
            return f"Current screen attached: {summary}"
        if action == "status":
            return self._format_status(data)
        if action == "start_session":
            return (
                f"Computer-use session started: session_id={data.get('session_id', '?')} "
                f"size={data.get('width', '?')}x{data.get('height', '?')}"
            )
        if action == "stop_session":
            return "Computer-use session stopped."
        if action == "move":
            return f"Pointer moved to x={data.get('x')} y={data.get('y')}."
        if action == "click":
            return f"Clicked {data.get('button', 'left')} button {data.get('count', 1)} time(s)."
        if action == "scroll":
            return f"Scrolled dx={data.get('dx', 0)} dy={data.get('dy', 0)}."
        if action == "key":
            keys = data.get("keys") or []
            return f"Sent keys: {keys!r}."
        if action == "type":
            text = str(data.get("text", "") or "")
            if data.get("submitted"):
                return f"Typed {len(text)} character(s) and submitted."
            return f"Typed {len(text)} character(s)."
        return str(data)

    def _format_error(self, result: dict[str, Any]) -> str:
        error = str(result.get("error") or "Unknown error")
        code = str(result.get("code") or "")
        if code == "COMPUTER_USE_REARM_REQUIRED" or error == "COMPUTER_USE_REARM_REQUIRED":
            detail = error if error and error != code else REARM_REQUIRED_DEFAULT_MESSAGE
            return (
                "COMPUTER_USE_REARM_REQUIRED: "
                f"{detail} Stop using computer_use_remote for now; ask the user to re-arm "
                "Computer Use in the A0 CLI with Confirm with User, approve the platform "
                "permission prompt if shown, then switch back to Free Run if desired. "
                "Do not retry or use screenshot fallbacks."
            )
        if code:
            return f"{code}: {error}"
        return error

    def _format_status(self, data: dict[str, Any]) -> str:
        status = str(data.get("status", "unknown") or "unknown")
        trust_mode = str(data.get("trust_mode", "") or "")
        backend_id = str(data.get("backend_id", "") or "").strip()
        backend_family = str(data.get("backend_family", "") or "").strip()
        active_contexts = data.get("active_contexts") or []
        active_text = ", ".join(str(item) for item in active_contexts) if active_contexts else "none"
        backend_text = ""
        rearm_guidance = ""
        if status == "rearm required":
            detail = str(data.get("last_error") or "").strip()
            if detail and detail != "COMPUTER_USE_REARM_REQUIRED":
                rearm_guidance = (
                    f" {detail} Stop using computer_use_remote until the user re-arms it."
                )
            else:
                rearm_guidance = (
                    " Computer Use is configured but the installed desktop-control backend "
                    "is not armed. "
                    "Stop using computer_use_remote until the user re-arms it."
                )
        if backend_id:
            backend_text = backend_id
            if backend_family:
                backend_text = f"{backend_text}/{backend_family}"
        if backend_text:
            return (
                f"Computer use status={status}, trust_mode={trust_mode or 'unknown'}, "
                f"backend={backend_text}, active_contexts={active_text}.{rearm_guidance}"
            )
        return (
            f"Computer use status={status}, trust_mode={trust_mode or 'unknown'}, "
            f"active_contexts={active_text}.{rearm_guidance}"
        )

    def _record_capture(self, data: dict[str, Any]) -> str:
        data = self._materialize_capture_artifact(data)
        _image_path, display_path = self._resolve_capture_path(data)
        width = data.get("width", "?")
        height = data.get("height", "?")
        capture_id = str(data.get("capture_id") or Path(display_path).stem or "?").strip()
        coordinate_space = str(data.get("coordinate_space") or "normalized_global_screen").strip()
        summary = (
            f"Computer-use capture id={capture_id} {width}x{height}, "
            f"coordinates={coordinate_space} [0,1]."
        )
        if data.get("fresh") is True:
            if "fresh_after_satisfied" in data:
                fresh_state = "confirmed" if data.get("fresh_after_satisfied") is not False else "not confirmed"
                summary = f"{summary} Fresh frame {fresh_state}."
            else:
                summary = f"{summary} Fresh capture requested."
        content = [
            {"type": "text", "text": summary},
            {"type": "image_url", "image_url": {"url": display_path}},
        ]
        raw_message = history.RawMessage(raw_content=content, preview=summary)
        self.agent.hist_add_message(False, content=raw_message, tokens=CAPTURE_TOKENS_ESTIMATE)
        self._prune_prior_capture_history()
        return summary

    def _prune_prior_capture_history(self) -> None:
        history_obj = getattr(self.agent, "history", None)
        if history_obj is None:
            return

        capture_messages = self._collect_capture_messages(history_obj)
        if len(capture_messages) <= 1:
            return

        latest = capture_messages[-1]
        for message in capture_messages[:-1]:
            if message is latest:
                continue
            preview = self._capture_preview_from_message(message)
            if not preview:
                continue
            message.content = f"{preview} [image reference superseded]"
            if hasattr(message, "summary"):
                message.summary = ""
            if hasattr(message, "calculate_tokens"):
                message.tokens = message.calculate_tokens()

    def _collect_capture_messages(self, history_obj: Any) -> list[Any]:
        messages: list[Any] = []

        def collect_topic(topic: Any) -> None:
            topic_messages = getattr(topic, "messages", None)
            if isinstance(topic_messages, list):
                for message in topic_messages:
                    if self._capture_preview_from_message(message):
                        messages.append(message)

        bulks = getattr(history_obj, "bulks", None)
        if isinstance(bulks, list):
            for bulk in bulks:
                self._collect_capture_messages_from_record(bulk, messages)

        topics = getattr(history_obj, "topics", None)
        if isinstance(topics, list):
            for topic in topics:
                collect_topic(topic)

        current = getattr(history_obj, "current", None)
        if current is not None:
            collect_topic(current)

        return messages

    def _collect_capture_messages_from_record(self, record: Any, messages: list[Any]) -> None:
        topic_messages = getattr(record, "messages", None)
        if isinstance(topic_messages, list):
            for message in topic_messages:
                if self._capture_preview_from_message(message):
                    messages.append(message)
            return

        nested_records = getattr(record, "records", None)
        if isinstance(nested_records, list):
            for nested in nested_records:
                self._collect_capture_messages_from_record(nested, messages)

    def _capture_preview_from_message(self, message: Any) -> str:
        content = getattr(message, "content", None)
        if not isinstance(content, dict):
            return ""
        raw_content = content.get("raw_content")
        preview = content.get("preview")
        if raw_content is None or not isinstance(preview, str):
            return ""
        if preview.startswith("Computer-use capture "):
            return preview
        return ""

    def _resolve_capture_path(self, data: dict[str, Any]) -> tuple[Path, str]:
        candidates = [
            str(data.get("path", "") or "").strip(),
            str(data.get("capture_path", "") or "").strip(),
            str(data.get("container_path", "") or "").strip(),
            str(data.get("host_path", "") or "").strip(),
        ]
        for candidate in candidates:
            if candidate and Path(candidate).exists():
                return Path(candidate), candidate
        raise FileNotFoundError(
            f"Capture artifact was not found in any advertised path: {candidates!r}"
        )

    def _materialize_capture_artifact(self, data: dict[str, Any]) -> dict[str, Any]:
        artifact = data.get("artifact")
        if not isinstance(artifact, dict):
            return data
        if str(artifact.get("encoding", "")).strip().lower() != "base64":
            return data

        encoded = str(artifact.get("data") or "")
        if not encoded:
            return data

        estimated_size = _estimated_base64_decoded_size(encoded)
        if estimated_size > MAX_CAPTURE_ARTIFACT_SIZE_BYTES:
            raise RuntimeError(
                "Computer-use capture artifact is too large to materialize safely "
                f"({estimated_size} bytes, limit {MAX_CAPTURE_ARTIFACT_SIZE_BYTES} bytes)."
            )

        filename = _safe_filename(str(artifact.get("filename") or "computer-use-capture.png"))
        context_id = str(getattr(getattr(self.agent, "context", None), "id", "") or "default")
        target_relative = str(Path(*COMPUTER_USE_CAPTURE_DIR, context_id, filename))
        target_path = Path(files.get_abs_path(target_relative))
        try:
            files.write_file_base64(target_relative, encoded)
        except Exception as exc:
            target_path.unlink(missing_ok=True)
            raise RuntimeError("Computer-use capture artifact could not be decoded.") from exc

        materialized = dict(data)
        materialized.pop("artifact", None)
        local_path = str(target_path)
        materialized["path"] = local_path
        materialized["a0_path"] = files.normalize_a0_path(local_path)
        materialized.setdefault("capture_path", local_path)
        materialized.setdefault("capture_id", target_path.stem)
        return materialized

    def _coerce_int(self, value: object, *, name: str) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name} must be an integer") from exc

    def _coerce_bool(self, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _safe_filename(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in value)
    cleaned = cleaned.strip("._") or f"computer-use-{uuid.uuid4().hex}.png"
    if "." not in cleaned:
        cleaned += ".png"
    return cleaned


def _estimated_base64_decoded_size(data: str) -> int:
    compact_length = sum(1 for char in data if not char.isspace())
    return (compact_length * 3) // 4
