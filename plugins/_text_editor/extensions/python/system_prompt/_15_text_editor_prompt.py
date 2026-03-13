from helpers.extension import Extension
from helpers import plugins
from agent import Agent, LoopData


class TextEditorPrompt(Extension):

    async def execute(
        self,
        system_prompt: list[str] = [],
        loop_data: LoopData = LoopData(),
        **kwargs,
    ):
        if not self.agent:
            return

        config = plugins.get_plugin_config("_text_editor", agent=self.agent) or {}
        default_line_count = config.get("default_line_count", 100)
        prompt = self.agent.read_prompt(
            "agent.system.tool.text_editor.md",
            default_line_count=default_line_count,
        )
        system_prompt.append(prompt)
