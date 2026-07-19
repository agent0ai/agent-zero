from __future__ import annotations

from typing import Any

from helpers.extension import Extension
from plugins._editor.helpers import markdown_sessions


class SyncOpenEditorSessionsAfterWorkdirMutation(Extension):
    async def execute(self, data: dict[str, Any] | None = None, **kwargs: Any):
        payload = data or {}
        paths = payload.get("paths")
        if not isinstance(paths, list):
            paths = [payload.get("path") or payload.get("current_path") or payload.get("parent_path")]
        markdown_sessions.get_manager().sync_external_file_mutations(
            [str(path) for path in paths if path],
        )
