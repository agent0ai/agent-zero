from helpers.extension import Extension
from plugins._browser.helpers.extension_sessions import finalize_extension_monologue


class FinalizeExtensionBrowserTurn(Extension):
    def execute(self, **kwargs):
        if self.agent:
            finalize_extension_monologue(self.agent, reason="completed")
