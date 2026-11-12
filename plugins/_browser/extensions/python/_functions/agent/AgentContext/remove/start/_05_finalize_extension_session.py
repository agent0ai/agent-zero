from helpers.extension import Extension
from plugins._browser.helpers.extension_sessions import finalize_extension_context


class FinalizeExtensionBrowserOnRemove(Extension):
    def execute(self, data: dict = {}, **kwargs):
        args = data.get("args", ())
        context_id = args[0] if isinstance(args, tuple) and args else ""
        if not context_id:
            return

        # The start hook runs before AgentContext removes the live context.
        from agent import AgentContext

        context = AgentContext.get(str(context_id))
        if context is not None:
            finalize_extension_context(
                context,
                reason="removed",
                retire=True,
                remove=True,
            )
