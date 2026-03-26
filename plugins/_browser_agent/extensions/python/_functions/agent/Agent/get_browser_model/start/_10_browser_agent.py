from helpers.extension import Extension
from plugins._browser_agent.helpers.browser_llm import build_browser_model_for_agent

class BrowserModelProvider(Extension):
    def execute(self, data: dict = {}, **kwargs):
        if self.agent:
            data["result"] = build_browser_model_for_agent(self.agent)
