from __future__ import annotations

from agent import LoopData
from helpers.extension import Extension
from plugins._editor.helpers import open_files_context


class IncludeEditorOpenFiles(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        if not self.agent or not self.agent.context:
            return

        context = open_files_context.build_context(self.agent.context.id)
        if not context:
            loop_data.extras_temporary.pop("editor_open_files", None)
            return

        loop_data.extras_temporary["editor_open_files"] = self.agent.read_prompt(
            "agent.extras.editor_open_files.md",
            editor_open_files=context,
        )
