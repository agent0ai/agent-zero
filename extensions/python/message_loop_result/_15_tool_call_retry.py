"""Retry rejected calls after optional plugins format their history entry."""

from dataclasses import replace
from typing import Any

from helpers.extension import Extension


class ToolCallRetry(Extension):
    def execute(self, result_data: dict[str, Any] | None = None, **kwargs: Any) -> None:
        if not self.agent or not isinstance(result_data, dict):
            return
        if result_data.get("skip_default_processing"):
            return
        params = self.agent.loop_data.params_temporary
        status = params.get("leaked_tool_call")
        if status not in {"rejected", "truncated"}:
            return

        llm_result = result_data["llm_result"]
        history_response = result_data.get("tool_call_retry_response", "{}")
        result_data["skip_default_processing"] = True
        log_item = params.get("log_item_generating")
        self.agent.hist_add_ai_response(
            history_response, id=log_item.id if log_item else "",
            llm_result=replace(llm_result, response=history_response, output_items=[]),
        )
        # A provider continuation would replay the original, unformatted output.
        if llm_result.mode == "responses" and llm_result.response_id:
            self.agent._clear_responses_pending_state()
        prompt = (
            "fw.msg_truncated_tool_call.md"
            if status == "truncated"
            else "fw.msg_leaked_tool_call.md"
        )
        warning = self.agent.read_prompt(prompt)
        warning_message = self.agent.hist_add_warning(message=warning)
        self.agent.context.log.log(
            type="warning",
            content=f"{self.agent.agent_name}: {warning}",
            id=warning_message.id,
        )
