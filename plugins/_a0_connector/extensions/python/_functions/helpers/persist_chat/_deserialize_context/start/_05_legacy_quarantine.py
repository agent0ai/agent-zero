from helpers.extension import Extension
from plugins._a0_connector.helpers.browser_bridge_legacy_quarantine import enabled, quarantine_document


class QuarantineLegacyDocument(Extension):
    def execute(self, data: dict, **kwargs):
        if enabled():
            document = data["kwargs"].get("data", data["args"][0] if data["args"] else None)
            quarantine_document(document)
