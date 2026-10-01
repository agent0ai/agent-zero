from helpers.extension import Extension
from plugins._browser.helpers.config import clear_browser_model


class BrowserModelCleanup(Extension):
    def execute(self, **kwargs):
        if self.agent:
            clear_browser_model(self.agent)
