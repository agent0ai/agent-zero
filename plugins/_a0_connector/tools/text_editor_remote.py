"""text_editor_remote tool - edit files on the CLI machine via `/ws`."""
from __future__ import annotations

import asyncio
import uuid
from typing import Any

from helpers.tool import Response, Tool
from helpers.ws import NAMESPACE
from helpers.ws_manager import ConnectionNotFoundError, get_shared_ws_manager

from plugins._a0_connector.helpers.text_editor_freshness import (
    apply_patch_post_state,
    check_patch_freshness,
    coerce_file_metadata,
    mark_file_state_stale,
    record_file_state,
)
from plugins._a0_connector.helpers.ws_runtime import (
    clear_pending_file_op,
    remote_file_metadata_for_sid,
    remote_tool_sids_for_context,
    select_remote_file_target_sid,
    store_pending_file_op,
)
from plugins._text_editor.helpers.patch_request import (
    exact_replace_to_patch_text,
    parse_patch_request,
)


FILE_OP_TIMEOUT = 30.0
FILE_OP_EVENT = "connector_file_op"
UNSUPPORTED_FRESHNESS_ERROR = (
    "text_editor_remote: the connected CLI is too old for freshness-aware patching. "
    "Upgrade the CLI and try again."
)


class TextEditorRemote(Tool):
    """Send file-editing operations to the connected CLI machine."""

    def get_log_object(self):
        action = str(self.args.get("action") or "")
        path = str(self.args.get("path") or "")
        verb = {"read": "Reading", "write": "Writing", "patch": "Patching"}.get(action)
        heading = (
            f"icon://construction {verb} {path} (remote)".strip()
            if verb and path
            else f"icon://construction {self.agent.agent_name}: Using tool '{self.name}' (remote)"
        )
        return self.agent.context.log.log(
            type="text_editor",
            heading=heading,
            content="",
            kvps=self.args,
            _tool_name=self.name,
            id=str(uuid.uuid4()),
        )

    async def execute(self, **kwargs: Any) -> Response:
        op = (
            str(
                self.args.get("action")
                or ""
            )
            .strip()
            .lower()
            .replace("-", "_")
        )
        if not op:
            return Response(
                message="action is required (read, write, or patch)",
                break_loop=False,
            )
        if op not in {"read", "write", "patch"}:
            return Response(
                message=f"Unknown action: {op!r}. Use read, write, or patch.",
                break_loop=False,
            )

        path = str(self.args.get("path", "")).strip()
        if not path:
            return Response(message="path is required", break_loop=False)

        if op == "read":
            payload: dict[str, Any] = {}
            if self.args.get("line_from"):
                payload["line_from"] = int(self.args["line_from"])
            if self.args.get("line_to"):
                payload["line_to"] = int(self.args["line_to"])
            result = await self._execute_file_op(op, path, **payload)
            self._record_success_state(result)
        elif op == "write":
            content = self.args.get("content")
            if content is None:
                return Response(
                    message="content is required for write",
                    break_loop=False,
                )
            result = await self._execute_file_op(op, path, content=content)
            self._record_success_state(result)
        else:
            patch_request, err = parse_patch_request(
                self.args.get("edits"),
                self.args.get("patch_text"),
                self.args.get("old_text"),
                self.args.get("new_text"),
                both_error=(
                    "provide exactly one patch form: edits, patch_text, "
                    "or old_text/new_text"
                ),
            )
            if err:
                return Response(
                    message=err,
                    break_loop=False,
                )
            if patch_request and patch_request.mode == "patch_text":
                result = await self._execute_context_patch(
                    path, patch_request.patch_text
                )
            elif patch_request and patch_request.mode == "replace":
                result = await self._execute_context_patch(
                    path,
                    exact_replace_to_patch_text(
                        path, patch_request.old_text, patch_request.new_text
                    ),
                )
            else:
                result = await self._execute_patch(
                    path,
                    patch_request.edits if patch_request else self.args.get("edits"),
                )

        return Response(
            message=self._extract_result(result, op, path),
            break_loop=False,
        )

    async def _execute_context_patch(self, path: str, patch_text: str) -> dict[str, Any]:
        patch_result = await self._execute_file_op("patch", path, patch_text=patch_text)
        if not self._result_ok(patch_result):
            return patch_result

        patch_file = self._extract_file_metadata(patch_result)
        if patch_file is not None:
            mark_file_state_stale(self.agent, patch_file)
        return patch_result

    async def _execute_patch(self, path: str, edits: Any) -> dict[str, Any]:
        stat_result = await self._execute_file_op("stat", path)
        if self._is_unsupported_cli_freshness(stat_result):
            return self._freshness_error(
                "unsupported_cli_freshness",
                UNSUPPORTED_FRESHNESS_ERROR,
            )
        if not self._result_ok(stat_result):
            return stat_result

        stat_file = self._extract_file_metadata(stat_result)
        if stat_file is None:
            return self._freshness_error(
                "unsupported_cli_freshness",
                UNSUPPORTED_FRESHNESS_ERROR,
            )

        freshness_code = check_patch_freshness(self.agent, stat_file)
        if freshness_code:
            return self._freshness_error(freshness_code)

        patch_result = await self._execute_file_op("patch", path, edits=edits)
        if not self._result_ok(patch_result):
            return patch_result

        patch_file = self._extract_file_metadata(patch_result)
        if patch_file is None:
            mark_file_state_stale(self.agent, stat_file)
        else:
            apply_patch_post_state(
                self.agent,
                patch_file,
                edits if isinstance(edits, list) else [],
            )
        return patch_result

    async def _execute_file_op(
        self,
        op: str,
        path: str,
        **payload_extra: Any,
    ) -> dict[str, Any]:
        context_id = self.agent.context.id
        require_writes = op in {"write", "patch"}
        candidates = remote_tool_sids_for_context(context_id)
        sid = select_remote_file_target_sid(context_id, require_writes=require_writes)
        if not sid:
            if not candidates:
                error = (
                    "text_editor_remote: no CLI client connected to Agent Zero. "
                    "Make sure the CLI is connected to this instance."
                )
            elif require_writes:
                write_blocked = any(
                    (metadata := remote_file_metadata_for_sid(candidate_sid))
                    and metadata.get("enabled", True)
                    and not metadata.get("write_enabled")
                    for candidate_sid in candidates
                )
                error = (
                    "text_editor_remote: no connected CLI currently allows remote file writes. "
                    "Press F3 to switch the CLI to Read&Write."
                    if write_blocked
                    else "text_editor_remote: no connected CLI currently advertises remote file access."
                )
            else:
                error = (
                    "text_editor_remote: no connected CLI currently advertises remote file access."
                )
            return {
                "ok": False,
                "error": error,
            }

        op_id = str(uuid.uuid4())
        payload: dict[str, Any] = {
            "op_id": op_id,
            "op": op,
            "path": path,
            "context_id": context_id,
        }
        payload.update(payload_extra)

        loop = asyncio.get_running_loop()
        future: asyncio.Future[dict[str, Any]] = loop.create_future()
        store_pending_file_op(
            op_id,
            sid=sid,
            future=future,
            loop=loop,
            context_id=context_id,
        )

        try:
            await get_shared_ws_manager().emit_to(
                NAMESPACE,
                sid,
                FILE_OP_EVENT,
                payload,
                handler_id=f"{self.__class__.__module__}.{self.__class__.__name__}",
            )
            result = await asyncio.wait_for(future, timeout=FILE_OP_TIMEOUT)
        except ConnectionNotFoundError:
            clear_pending_file_op(op_id)
            return {
                "op_id": op_id,
                "ok": False,
                "error": (
                    "text_editor_remote: the selected CLI client disconnected before "
                    "the file operation could be delivered"
                ),
            }
        except asyncio.TimeoutError:
            clear_pending_file_op(op_id)
            return {
                "op_id": op_id,
                "ok": False,
                "error": (
                    f"text_editor_remote: timed out waiting for CLI to respond "
                    f"to {op} on {path!r}"
                ),
            }
        except Exception as exc:
            clear_pending_file_op(op_id)
            return {
                "op_id": op_id,
                "ok": False,
                "error": f"text_editor_remote: error sending file_op: {exc}",
            }
        finally:
            clear_pending_file_op(op_id)

        if isinstance(result, dict):
            return result

        return {
            "op_id": op_id,
            "ok": False,
            "error": f"Unexpected response format from CLI: {result!r}",
        }

    def _record_success_state(self, result: Any) -> None:
        if not self._result_ok(result):
            return

        file_meta = self._extract_file_metadata(result)
        if file_meta is not None:
            record_file_state(self.agent, file_meta)

    def _extract_file_metadata(self, result: Any) -> dict[str, Any] | None:
        if not isinstance(result, dict):
            return None

        data = result.get("result")
        if not isinstance(data, dict):
            return None

        return coerce_file_metadata(data.get("file"))

    def _freshness_error(self, code: str, error: str = "") -> dict[str, Any]:
        return {"ok": False, "code": code, "error": error}

    def _result_ok(self, result: Any) -> bool:
        return isinstance(result, dict) and bool(result.get("ok"))

    def _is_unsupported_cli_freshness(self, result: Any) -> bool:
        if not isinstance(result, dict) or bool(result.get("ok")):
            return False

        error = str(result.get("error") or "").strip().lower()
        return "unknown op: stat" in error

    def _extract_result(self, result: Any, op: str, path: str) -> str:
        if not isinstance(result, dict):
            return f"Unexpected response format from CLI: {result!r}"

        ok = bool(result.get("ok"))
        data = result.get("result")
        error = result.get("error")
        code = str(result.get("code") or "").strip().lower()

        if not ok:
            if code == "patch_need_read":
                return self.agent.read_prompt(
                    "fw.text_editor.patch_need_read.md",
                    path=path,
                )
            if code == "patch_stale_read":
                return self.agent.read_prompt(
                    "fw.text_editor.patch_stale_read.md",
                    path=path,
                )
            if code == "unsupported_cli_freshness":
                return str(error or UNSUPPORTED_FRESHNESS_ERROR)
            return f"Error ({op} {path!r}): {error or 'Unknown error'}"

        if not isinstance(data, dict):
            data = {}

        if op == "read":
            content = data.get("content", "")
            total_lines = data.get("total_lines", "?")
            return f"{path} {total_lines} lines\n>>>\n{content}\n<<<"
        if op == "write":
            return data.get("message") or f"{path} written successfully"
        if op == "patch":
            return data.get("message") or f"{path} patched successfully"
        return str(data)
