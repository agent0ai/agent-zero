from helpers.extension import Extension
from plugins._browser.helpers.config import (
    browser_model_is_active,
    resolve_browser_model,
)


class BrowserModelProvider(Extension):
    def execute(self, data: dict = {}, **kwargs):
        if self.agent and browser_model_is_active(self.agent):
            data["result"] = resolve_browser_model(
                self.agent,
                fallback=data.get("result"),
            )
