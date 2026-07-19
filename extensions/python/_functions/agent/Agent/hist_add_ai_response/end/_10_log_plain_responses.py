from typing import Any

from helpers import extract_tools
from helpers.extension import Extension


class LogPlainResponses(Extension):
    def execute(self, data: dict[str, Any] | None = None, **kwargs):
        if not self.agent or not isinstance(data, dict):
            return

        call_kwargs = data.get("kwargs")
        if not isinstance(call_kwargs, dict):
            call_kwargs = {}

        llm_result = call_kwargs.get("llm_result")
        if getattr(llm_result, "mode", "") != "responses":
            return

        message = call_kwargs.get("message")
        call_args = data.get("args")
        if message is None and isinstance(call_args, tuple) and len(call_args) > 1:
            message = call_args[1]
        if not isinstance(message, str) or not message:
            return
        if extract_tools.json_parse_dirty(message) is not None:
            return

        params = getattr(getattr(self.agent, "loop_data", None), "params_temporary", None)
        if not isinstance(params, dict) or "log_item_response" in params:
            return

        log_item = params.get("log_item_generating")
        if log_item is None:
            return

        params["log_item_response"] = log_item
        log_item.update(
            type="response",
            heading="",
            content=message,
            finished=True,
            update_progress="none",
        )
