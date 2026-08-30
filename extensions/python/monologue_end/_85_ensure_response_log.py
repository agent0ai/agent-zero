import json
from typing import Any

from helpers.extension import Extension


class EnsureResponseLog(Extension):
    async def execute(self, loop_data: Any = None, **kwargs):
        if not self.agent:
            return

        if not loop_data:
            return

        if "log_item_response" in loop_data.params_temporary:
            return

        gen_item = loop_data.params_temporary.get("log_item_generating")
        if not gen_item:
            return

        response_text = self._get_latest_ai_response_text()
        if not response_text:
            return

        loop_data.params_temporary["log_item_response"] = self.agent.context.log.log(
            type="response",
            heading=f"icon://chat {self.agent.agent_name}: Responding",
            content=response_text,
            id=getattr(gen_item, "id", "") or "",
        )

    def _get_latest_ai_response_text(self) -> str:
        try:
            topic = self.agent.history.current if self.agent else None
            messages = topic.messages if topic else []
            for message in reversed(messages):
                if message.ai and message.content:
                    return self._normalize_response_content(message.content)
            return ""
        except Exception:
            return ""

    @staticmethod
    def _normalize_response_content(content) -> str:
        if isinstance(content, dict):
            tool_name = content.get("tool_name")
            if tool_name and tool_name != "response":
                return ""

            if isinstance(content.get("tool_args"), dict):
                text = content["tool_args"].get("text")
                if text:
                    return str(text)

            if content.get("text"):
                return str(content["text"])

            if tool_name == "response":
                return ""

            return str(content)

        if not isinstance(content, str):
            return str(content)

        stripped = content.strip()
        try:
            parsed = json.loads(stripped)
        except Exception:
            return stripped

        if isinstance(parsed, dict):
            return EnsureResponseLog._normalize_response_content(parsed)
        return stripped
