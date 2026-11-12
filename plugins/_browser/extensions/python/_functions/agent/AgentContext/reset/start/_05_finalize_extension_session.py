from helpers.extension import Extension
from plugins._browser.helpers.extension_sessions import finalize_extension_context


class FinalizeExtensionBrowserOnReset(Extension):
    def execute(self, data: dict = {}, **kwargs):
        args = data.get("args", ())
        context = args[0] if isinstance(args, tuple) and args else None
        if context is not None:
            finalize_extension_context(
                context,
                reason="reset",
                retire=True,
            )
