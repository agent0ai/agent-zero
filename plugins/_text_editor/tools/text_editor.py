from helpers.tool import Tool, Response
from helpers.extension import call_extensions_async
from helpers import plugins, runtime
from plugins._text_editor.helpers.file_ops import (
    FileInfo,
    read_file,
    write_file,
    validate_edits,
    apply_patch,
    apply_context_patch_file,
    apply_exact_replace_file,
    file_info,
)
from plugins._text_editor.helpers.patch_request import parse_patch_request
from plugins._text_editor.helpers.patch_state import (
    LOCAL_FRESHNESS_KEY,
    apply_patch_post_state,
    check_patch_freshness,
    mark_file_state_stale,
    record_file_state,
)

# Key used in agent.data to store file state for patch validation
# Value: {path: {"mtime": float, "total_lines": int}}
_MTIME_KEY = LOCAL_FRESHNESS_KEY



class TextEditor(Tool):

    async def execute(self, **kwargs):
        action = _current_action(self, kwargs)
        if action == "read":
            return await self._read(**kwargs)
        elif action == "write":
            return await self._write(**kwargs)
        elif action == "patch":
            return await self._patch(**kwargs)
        return Response(
            message=(
                f"unknown action '{action or self.method or ''}'. "
                "Supported actions: read, write, patch."
            ),
            break_loop=False,
        )

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------
    async def _read(self, path: str = "", **kwargs) -> Response:
        if not path:
            return self._error("read", path, "path is required")

        cfg = _get_config(self.agent)
        line_from = int(kwargs.get("line_from", 1))
        raw_to = kwargs.get("line_to")
        line_to = int(raw_to) if raw_to is not None else None

        result = await runtime.call_development_function(
            read_file,
            path,
            line_from=line_from,
            line_to=line_to,
            max_line_tokens=cfg["max_line_tokens"],
            default_line_count=cfg["default_line_count"],
            max_total_read_tokens=cfg["max_total_read_tokens"],
        )

        if result["error"]:
            return self._error("read", path, result["error"])

        info = await runtime.call_development_function(file_info, path)
        record_file_state(
            self.agent,
            info,
            key=_MTIME_KEY,
            total_lines=result["total_lines"],
        )

        # Extension point
        ext_data = {
            "content": result["content"],
            "warnings": result["warnings"],
        }
        await call_extensions_async(
            "text_editor_read_after", agent=self.agent, data=ext_data
        )

        msg = self.agent.read_prompt(
            "fw.text_editor.read_ok.md",
            path=info["expanded"],
            total_lines=str(result["total_lines"]),
            warnings=ext_data["warnings"],
            content=ext_data["content"],
        )
        return Response(message=msg, break_loop=False)

    # ------------------------------------------------------------------
    # WRITE
    # ------------------------------------------------------------------
    async def _write(
        self, path: str = "", content: str | None = "", **kwargs
    ) -> Response:
        if not path:
            return self._error("write", path, "path is required")

        # Extension point
        ext_data = {"path": path, "content": content}
        await call_extensions_async(
            "text_editor_write_before", agent=self.agent, data=ext_data
        )

        result = await runtime.call_development_function(
            write_file, ext_data["path"], ext_data["content"]
        )

        if result["error"]:
            return self._error("write", path, result["error"])

        # Extension point
        await call_extensions_async(
            "text_editor_write_after", agent=self.agent,
            data={"path": path, "total_lines": result["total_lines"]},
        )

        info = await runtime.call_development_function(file_info, path)
        record_file_state(
            self.agent,
            info,
            key=_MTIME_KEY,
            total_lines=result["total_lines"],
        )

        cfg = _get_config(self.agent)
        read_result = await runtime.call_development_function(
            read_file,
            info["expanded"],
            line_from=1,
            line_to=result["total_lines"],
            max_line_tokens=cfg["max_line_tokens"],
            max_total_read_tokens=cfg["max_total_read_tokens"],
        )

        msg = self.agent.read_prompt(
            "fw.text_editor.write_ok.md",
            path=info["expanded"],
            total_lines=str(result["total_lines"]),
            content=read_result["content"],
        )
        return Response(message=msg, break_loop=False)

    # ------------------------------------------------------------------
    # PATCH
    # ------------------------------------------------------------------
    async def _patch(
        self, path: str = "", edits=None, patch_text=None, old_text=None, new_text=None, **kwargs
    ) -> Response:
        if not path:
            return self._error("patch", path, "path is required")
        patch_request, err = parse_patch_request(
            edits,
            patch_text,
            old_text,
            new_text,
            missing_error="",
        )
        if err:
            return self._error("patch", path, err)

        info = await runtime.call_development_function(file_info, path)
        if not info["is_file"]:
            return self._error("patch", path, "file not found")

        expanded = info["expanded"]

        if patch_request and patch_request.mode == "patch_text":
            return await self._patch_context(
                path, expanded, patch_request.patch_text
            )
        if patch_request and patch_request.mode == "replace":
            return await self._patch_replace(
                path, expanded, patch_request.old_text, patch_request.new_text
            )

        return await self._patch_edits(
            path,
            expanded,
            info,
            patch_request.edits if patch_request else edits,
        )

    async def _patch_edits(
        self, path: str, expanded: str, info: FileInfo, edits
    ) -> Response:
        freshness_code = check_patch_freshness(self.agent, info, key=_MTIME_KEY)
        if freshness_code:
            return self._error(
                "patch",
                path,
                _freshness_error_message(self.agent, info, freshness_code),
            )

        parsed, err = validate_edits(edits)
        if err:
            return self._error("patch", path, err)

        # Extension point
        ext_data = {"path": expanded, "edits": parsed}
        await call_extensions_async(
            "text_editor_patch_before", agent=self.agent, data=ext_data
        )

        try:
            total_lines = await runtime.call_development_function(
                apply_patch, ext_data["path"], ext_data["edits"]
            )
        except Exception as exc:
            return self._error("patch", path, str(exc))

        # Extension point
        await call_extensions_async(
            "text_editor_patch_after", agent=self.agent,
            data={"path": expanded, "total_lines": total_lines},
        )

        # Refresh file info after patch for updated mtime
        post_info = await runtime.call_development_function(
            file_info, expanded
        )
        apply_patch_post_state(
            self.agent,
            post_info,
            ext_data["edits"],
            key=_MTIME_KEY,
            total_lines=total_lines,
        )

        patch_content = await _read_patch_region(
            expanded, ext_data["edits"], total_lines, _get_config(self.agent)
        )

        msg = self.agent.read_prompt(
            "fw.text_editor.patch_ok.md",
            path=expanded,
            edit_count=str(len(edits or [])),
            total_lines=str(total_lines),
            content=patch_content,
        )
        return Response(message=msg, break_loop=False)

    async def _patch_replace(
        self, path: str, expanded: str, old_text: str, new_text: str
    ) -> Response:
        # Extension point
        ext_data = {
            "path": expanded,
            "old_text": old_text,
            "new_text": new_text,
            "edits": [],
            "mode": "replace",
        }
        await call_extensions_async(
            "text_editor_patch_before", agent=self.agent, data=ext_data
        )

        try:
            result = await runtime.call_development_function(
                apply_exact_replace_file,
                ext_data["path"],
                ext_data["old_text"],
                ext_data["new_text"],
            )
        except Exception as exc:
            return self._error("patch", path, str(exc))

        total_lines = result["total_lines"]

        await call_extensions_async(
            "text_editor_patch_after", agent=self.agent,
            data={
                "path": ext_data["path"],
                "total_lines": total_lines,
                "replacement_count": result["replacement_count"],
                "mode": "replace",
            },
        )

        post_info = await runtime.call_development_function(
            file_info, ext_data["path"]
        )
        mark_file_state_stale(self.agent, post_info, key=_MTIME_KEY)

        patch_content = await _read_exact_replace_region(
            ext_data["path"], result, _get_config(self.agent)
        )

        msg = self.agent.read_prompt(
            "fw.text_editor.patch_ok.md",
            path=ext_data["path"],
            edit_count=str(result["replacement_count"]),
            total_lines=str(total_lines),
            content=patch_content,
        )
        return Response(message=msg, break_loop=False)

    async def _patch_context(
        self, path: str, expanded: str, patch_text
    ) -> Response:
        patch_text = str(patch_text)
        if not patch_text.strip():
            return self._error("patch", path, "patch_text must not be empty")

        # Extension point
        ext_data = {
            "path": expanded,
            "patch_text": patch_text,
            "edits": [],
            "mode": "patch_text",
        }
        await call_extensions_async(
            "text_editor_patch_before", agent=self.agent, data=ext_data
        )

        try:
            result = await runtime.call_development_function(
                apply_context_patch_file,
                ext_data["path"],
                ext_data["patch_text"],
            )
        except Exception as exc:
            return self._error("patch", path, str(exc))

        total_lines = result["total_lines"]

        # Extension point
        await call_extensions_async(
            "text_editor_patch_after", agent=self.agent,
            data={
                "path": ext_data["path"],
                "total_lines": total_lines,
                "hunk_count": result["hunk_count"],
                "mode": "patch_text",
            },
        )

        post_info = await runtime.call_development_function(
            file_info, ext_data["path"]
        )
        mark_file_state_stale(self.agent, post_info, key=_MTIME_KEY)

        patch_content = await _read_context_patch_region(
            ext_data["path"], result, _get_config(self.agent)
        )

        msg = self.agent.read_prompt(
            "fw.text_editor.patch_ok.md",
            path=ext_data["path"],
            edit_count=str(result["hunk_count"]),
            total_lines=str(total_lines),
            content=patch_content,
        )
        return Response(message=msg, break_loop=False)

    # ------------------------------------------------------------------
    # Shared error helper
    # ------------------------------------------------------------------
    def _error(self, action: str, path: str, error: str) -> Response:
        msg = self.agent.read_prompt(
            f"fw.text_editor.{action}_error.md", path=path, error=error
        )
        return Response(message=msg, break_loop=False)


# ------------------------------------------------------------------
# Standalone helpers
# ------------------------------------------------------------------

async def _read_patch_region(
    path: str, edits: list[dict], total_lines: int, cfg: dict
) -> str:
    if not edits:
        return ""

    min_from = min(e["from"] for e in edits)
    added = sum(
        e["content"].count("\n")
        + (1 if e["content"] and not e["content"].endswith("\n") else 0)
        for e in edits if e.get("content")
    )
    removed = sum(
        max(e["to"] - e["from"] + 1, 0)
        for e in edits if not e.get("insert")
    )
    max_to = max(e["to"] for e in edits)
    end_line = max_to + added - removed + 3

    result = await runtime.call_development_function(
        read_file,
        path,
        line_from=max(min_from - 1, 1),
        line_to=min(end_line, total_lines),
        max_line_tokens=cfg["max_line_tokens"],
        max_total_read_tokens=cfg["max_total_read_tokens"],
    )
    return result["content"]


async def _read_context_patch_region(
    path: str, result: dict, cfg: dict
) -> str:
    total_lines = int(result["total_lines"])
    if total_lines <= 0:
        return ""

    line_from = min(max(int(result["line_from"]), 1), total_lines)
    line_to = min(max(int(result["line_to"]), line_from) + 3, total_lines)

    read_result = await runtime.call_development_function(
        read_file,
        path,
        line_from=max(line_from - 1, 1),
        line_to=line_to,
        max_line_tokens=cfg["max_line_tokens"],
        max_total_read_tokens=cfg["max_total_read_tokens"],
    )
    return read_result["content"]


async def _read_exact_replace_region(
    path: str, result: dict, cfg: dict
) -> str:
    total_lines = int(result["total_lines"])
    if total_lines <= 0:
        return ""

    line_from = min(max(int(result["line_from"]), 1), total_lines)
    line_to = min(max(int(result["line_to"]), line_from) + 3, total_lines)

    read_result = await runtime.call_development_function(
        read_file,
        path,
        line_from=max(line_from - 1, 1),
        line_to=line_to,
        max_line_tokens=cfg["max_line_tokens"],
        max_total_read_tokens=cfg["max_total_read_tokens"],
    )
    return read_result["content"]


def _freshness_error_message(agent, info: FileInfo, code: str) -> str:
    prompt = (
        "fw.text_editor.patch_stale_read.md"
        if code == "patch_stale_read"
        else "fw.text_editor.patch_need_read.md"
    )
    return agent.read_prompt(prompt, path=info["expanded"])

# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------

def _get_config(agent) -> dict:
    config = plugins.get_plugin_config("_text_editor", agent=agent) or {}
    return {
        "max_line_tokens": int(config.get("max_line_tokens", 500)),
        "default_line_count": int(config.get("default_line_count", 100)),
        "max_total_read_tokens": int(config.get("max_total_read_tokens", 4000)),
    }


def _current_action(tool: TextEditor, kwargs: dict) -> str:
    return (
        str(
            kwargs.get("action")
            or tool.args.get("action")
            or ""
        )
        .strip()
        .lower()
        .replace("-", "_")
    )
