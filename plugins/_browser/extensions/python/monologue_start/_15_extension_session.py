from helpers.extension import Extension
from plugins._browser.helpers.extension_sessions import begin_extension_monologue


class BeginExtensionBrowserTurn(Extension):
    def execute(self, **kwargs):
        if self.agent:
            begin_extension_monologue(self.agent)
