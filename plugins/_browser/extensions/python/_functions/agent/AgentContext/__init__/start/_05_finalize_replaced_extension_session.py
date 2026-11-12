from helpers.extension import Extension
from plugins._browser.helpers.extension_sessions import finalize_extension_context


class FinalizeReplacedExtensionBrowserContext(Extension):
    def execute(self, data: dict = {}, **kwargs):
        args = data.get("args", ())
        call_kwargs = data.get("kwargs", {})
        if not isinstance(args, tuple) or not args:
            return
        if not isinstance(call_kwargs, dict):
            call_kwargs = {}

        candidate = args[0]
        context_id = call_kwargs.get("id")
        if context_id is None and len(args) > 2:
            context_id = args[2]
        if not context_id:
            return

        # Import lazily: this hook executes while agent.py is constructing a
        # context and must not introduce a module-import cycle.
        from agent import AgentContext

        existing = AgentContext.get(str(context_id))
        if existing is not None and existing is not candidate:
            finalize_extension_context(
                existing,
                reason="replaced",
            )
