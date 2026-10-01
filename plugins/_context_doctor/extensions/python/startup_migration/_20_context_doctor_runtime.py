from helpers.extension import Extension
from helpers.plugins import call_plugin_hook


class ContextDoctorRuntime(Extension):
    def execute(self, **kwargs):
        call_plugin_hook(
            "_context_doctor",
            "ensure_dependencies",
            raise_on_error=False,
        )
