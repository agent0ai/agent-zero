"""Show public commentary beside native calls in the completed generation log."""
import json

from helpers.extension import Extension
from extensions.python.before_main_llm_call._10_log_for_stream import build_heading


class NativeThoughts(Extension):
    def execute(self, result_data, loop_data, **kwargs):
        if not self.agent or result_data.get("skip_default_processing"):
            return
        result = result_data["llm_result"]
        log_item = loop_data.params_temporary.get("log_item_generating")
        if not result.function_calls or log_item is None:
            return
        thoughts = []
        for item in result.output_items:
            if (item.type != "message" or item.data.get("phase") not in (None, "commentary")
                    or item.data.get("role") not in (None, "assistant")):
                continue
            content = item.data.get("content")
            if not isinstance(content, list):
                continue
            text = "".join(block["text"] for block in content
                           if isinstance(block, dict) and block.get("type") == "output_text"
                           and isinstance(block.get("text"), str)).strip()
            if text:
                thoughts.append(text)
        if not thoughts:
            return
        action = {"thoughts": thoughts, **json.loads(result.function_calls_text())}
        kvps = {**(log_item.kvps or {}), **action}
        kvps.pop("step", None)
        log_item.update(heading=build_heading(self.agent, f"Using {action['tool_name']}"),
                        content=json.dumps(action, ensure_ascii=False), kvps=kvps)
