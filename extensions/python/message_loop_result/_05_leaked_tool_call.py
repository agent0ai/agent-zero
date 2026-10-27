"""Recover complete alternate-format calls before normal output repair."""

from __future__ import annotations

import json
from typing import Any

from helpers.extension import Extension
from helpers.extract_tools import extract_leaked_tool_request, normalize_tool_request
from helpers.responses_tools import build_responses_function_tools, original_tool_name


class LeakedToolCall(Extension):
    def execute(self, result_data: dict[str, Any] | None = None, **kwargs: Any) -> None:
        if not self.agent or not isinstance(result_data, dict):
            return
        if result_data.get("skip_default_processing"):
            return
        llm_result = result_data.get("llm_result")
        # Actual transport tool calls remain authoritative; never execute text
        # alongside them or interfere with provider-native continuation items.
        if getattr(llm_result, "function_calls", None) or getattr(
            llm_result, "builtin_items", None
        ):
            return
        response = getattr(llm_result, "response", None)
        if not isinstance(response, str) or not response:
            return

        _, request = extract_leaked_tool_request(response)
        if request is None:
            return
        try:
            if getattr(llm_result, "mode", None) == "chat_completions":
                _, name_map = build_responses_function_tools(self.agent)
            else:
                name_map = self.agent.get_data("responses_tool_name_map")
            if not isinstance(name_map, dict) or not all(
                isinstance(key, str) and isinstance(name, str)
                for key, name in name_map.items()
            ):
                return
            request["tool_name"] = original_tool_name(request["tool_name"], name_map)
            name, args = normalize_tool_request(request)
            name = original_tool_name(name, name_map)
            if name not in name_map.values():
                return
        except Exception:
            return  # Failed conversion must leave the normal repair path available.
        llm_result.response = json.dumps(
            {"tool_name": name, "tool_args": args}, ensure_ascii=False, separators=(",", ":")
        )
        self.agent.context.log.log(
            type="info", content="Recovered a complete leaked tool call."
        )
