from helpers.extension import Extension
from helpers.plugins import call_plugin_hook


class LocalTtsEnabled(Extension):
    def execute(self, data: dict, **kwargs):
        if data.get("exception"):
            return
        args, values = data["args"], data["kwargs"]
        name = values.get("plugin_name", args[0] if args else "")
        enabled = values.get("enabled", args[1] if len(args) > 1 else False)
        if name == "_kokoro_tts" and enabled:
            call_plugin_hook("_kokoro_tts", "ensure_dependencies", raise_on_error=False)
