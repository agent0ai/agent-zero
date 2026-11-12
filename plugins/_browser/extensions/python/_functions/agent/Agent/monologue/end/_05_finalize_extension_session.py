from helpers.extension import Extension
from plugins._browser.helpers.extension_sessions import finalize_extension_monologue


class FinalizeExtensionBrowserAfterMonologueEscape(Extension):
    def execute(self, data: dict = {}, **kwargs):
        args = data.get("args", ())
        agent = args[0] if isinstance(args, tuple) and args else self.agent
        if agent is None:
            return
        reason = "failed" if isinstance(data.get("exception"), BaseException) else "completed"
        finalize_extension_monologue(agent, reason=reason)
