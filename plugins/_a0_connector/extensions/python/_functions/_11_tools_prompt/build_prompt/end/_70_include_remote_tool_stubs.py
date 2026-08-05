from __future__ import annotations

import re
from typing import Any

from helpers.extension import Extension
from helpers.tool_policy import resolve_tool
from plugins._a0_connector.helpers.remote_tool_prompts import (
    REMOTE_TOOL_PROMPTS,
    remote_tool_prompt_availability,
)


class IncludeRemoteToolStubs(Extension):
    def execute(self, data: dict[str, Any] = {}, **kwargs: Any) -> None:
        if self.agent is None:
            return
        if not isinstance(data, dict):
            return
        result = data.get("result")
        if not isinstance(result, str):
            return

        context_id = str(
            getattr(getattr(self.agent, "context", None), "id", "") or ""
        ).strip()
        if not context_id:
            return

        available = remote_tool_prompt_availability(context_id)
        for tool_name, prompt_file in REMOTE_TOOL_PROMPTS.items():
            try:
                prompt = self.agent.read_prompt(prompt_file).strip()
            except Exception:
                continue
            if not prompt:
                continue

            if available.get(tool_name) and resolve_tool(self.agent, tool_name).allowed:
                marker = f'"tool_name": "{tool_name}"'
                if marker not in result:
                    result = f"{result.rstrip()}\n\n{prompt}"
                continue

            result = _remove_prompt(result, prompt)

        data["result"] = result


def _remove_prompt(result: str, prompt: str) -> str:
    if prompt not in result:
        return result

    return re.sub(r"\n{3,}", "\n\n", result.replace(prompt, "")).rstrip()
