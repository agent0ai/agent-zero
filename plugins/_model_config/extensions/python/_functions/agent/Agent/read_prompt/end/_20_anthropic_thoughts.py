from helpers.extension import Extension
from plugins._model_config.helpers.model_config import get_chat_model_config


class AnthropicThoughts(Extension):
    def execute(self, data: dict, **kwargs):
        if not self.agent or not isinstance(data.get("result"), str):
            return
        args = data["args"]
        name = args[1] if len(args) > 1 else data["kwargs"].get("file")
        if name not in {
            "agent.system.main.md",
            "agent.system.main.communication.md",
            "agent.system.main.solving.md",
        }:
            return
        config = get_chat_model_config(self.agent)
        if "anthropic" not in f"{config.get('provider', '')}/{config.get('name', '')}".lower():
            return
        data["result"] = data["result"].replace(
            "- thoughts: array thoughts before execution in natural language",
            "- thoughts: array of brief public action summaries; do not disclose private internal reasoning",
        ).replace(
            "explain each step in thoughts",
            "give brief public progress updates in thoughts, not private internal reasoning",
        )
