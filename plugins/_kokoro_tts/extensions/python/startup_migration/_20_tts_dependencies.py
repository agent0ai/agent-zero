from helpers.extension import Extension
from helpers.plugins import call_plugin_hook


class LocalTtsDependencies(Extension):
    def execute(self, **kwargs):
        call_plugin_hook("_kokoro_tts", "ensure_dependencies", raise_on_error=False)
