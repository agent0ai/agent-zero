from helpers.extension import Extension
from plugins._a0_connector.helpers.browser_bridge_legacy_quarantine import enabled, quarantine_context


class QuarantineLegacyContext(Extension):
    def execute(self, data: dict, **kwargs):
        if enabled():
            context = data["kwargs"].get("context", data["args"][0] if data["args"] else None)
            quarantine_context(context)
