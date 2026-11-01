"""Retry empty turns and keep non-action text in the current generation."""

from __future__ import annotations

import json
from typing import Any

from helpers import extract_tools
from helpers.errors import HandledException
from helpers.extension import Extension
from helpers.print_style import PrintStyle
from helpers.settings import get_settings


STATE_KEY = "_unusable_response_failures"


class EmptyResponse(Extension):
    def execute(self, result_data: dict[str, Any] | None = None, **kwargs: Any) -> None:
        if not self.agent or not isinstance(result_data, dict):
            return
        if result_data.get("skip_default_processing"):
            return

        llm_result = result_data.get("llm_result")
        if getattr(llm_result, "function_calls", None) or getattr(llm_result, "builtin_items", None):
            return
        response = getattr(llm_result, "response", "")
        reasoning = getattr(llm_result, "reasoning", "")
        if not isinstance(response, str) or not isinstance(reasoning, str):
            return
        has_response = bool(response.strip())
        if has_response:
            if extract_tools.extract_tool_request(response) is not None:
                return
            status, _ = extract_tools.extract_leaked_tool_request(response)
            if status not in ("clean", "quoted"):
                return  # Malformed tool intent keeps its repair/dispatch path.

        if has_response or reasoning.strip():
            text = response if has_response else reasoning
            parsed = extract_tools.json_parse_dirty(response) or {}
            thoughts = parsed.get("thoughts")
            if not isinstance(thoughts, list) or not thoughts:
                thoughts = [text]
            log_item = self.agent.loop_data.params_temporary.get("log_item_generating")
            self.agent.hist_add_ai_response(
                response if has_response else json.dumps(
                    {"thoughts": thoughts}, ensure_ascii=False, separators=(",", ":"),
                ),
                id=log_item.id if log_item else "",
                llm_result=llm_result,
            )
            if log_item is not None:
                log_item.update(content=text, thoughts=thoughts)
            warning = self.agent.read_prompt(
                "fw.msg_misformat.md" if has_response else "fw.msg_reasoning_only.md"
            )
            self.agent.hist_add_warning(message=warning)
            result_data["skip_default_processing"] = True
            return

        warning = self.agent.read_prompt("fw.msg_empty_response.md")
        PrintStyle(font_color="orange", padding=True).print(warning)
        state = self.agent.loop_data.params_persistent
        previous = state.get(STATE_KEY, {})
        previous_iteration = previous.get("iteration") if isinstance(previous, dict) else None
        count = (
            previous.get("count", 0) + 1
            if previous_iteration == self.agent.loop_data.iteration - 1
            else 1
        )
        state[STATE_KEY] = {"iteration": self.agent.loop_data.iteration, "count": count}
        limit = get_settings()["max_consecutive_unusable_responses"]
        if count >= limit:
            stop_message = self.agent.read_prompt(
                "fw.msg_unusable_response_limit.md", limit=limit
            )
            self.agent.context.log.log(type="warning", content=stop_message)
            raise HandledException(stop_message)
        self.agent.context.log.log(
            type="warning",
            content=warning,
        )
        result_data["skip_default_processing"] = True
