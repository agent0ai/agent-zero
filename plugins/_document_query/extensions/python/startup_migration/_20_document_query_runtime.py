from helpers.extension import Extension
from helpers.plugins import call_plugin_hook


class DocumentQueryRuntime(Extension):
    def execute(self, **kwargs):
        call_plugin_hook(
            "_document_query",
            "ensure_dependencies",
            raise_on_error=False,
        )

