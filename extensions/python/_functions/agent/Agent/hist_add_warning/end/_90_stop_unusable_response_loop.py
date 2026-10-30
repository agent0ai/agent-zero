from helpers import response_recovery
from helpers.errors import HandledException
from helpers.extension import Extension
from helpers.settings import get_settings

STATE_KEY = response_recovery.STATE_KEY


class StopUnusableResponseLoop(Extension):
    def execute(self, data: dict | None = None, **kwargs):
        if not self.agent or not isinstance(data, dict):
            return

        call_kwargs = data.get("kwargs")
        message = call_kwargs.get("message") if isinstance(call_kwargs, dict) else None
        call_args = data.get("args")
        if message is None and isinstance(call_args, tuple) and len(call_args) > 1:
            message = call_args[1]

        if not isinstance(message, str):
            return
        if message not in {
            self.agent.read_prompt("fw.msg_misformat.md"),
            self.agent.read_prompt("fw.msg_repeat.md"),
            self.agent.read_prompt("fw.msg_empty_response.md"),
            self.agent.read_prompt("fw.msg_reasoning_only.md"),
            self.agent.read_prompt("fw.msg_thoughts_fallback.md"),
            self.agent.read_prompt("fw.msg_output_limit.md"),
        }:
            return

        stop: HandledException | None = response_recovery.record_unusable_response(
            self.agent, get_settings()["max_consecutive_unusable_responses"]
        )
        if stop is not None:
            data["exception"] = stop
