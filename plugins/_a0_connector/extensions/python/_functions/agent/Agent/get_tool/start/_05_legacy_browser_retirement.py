from helpers.extension import Extension
from plugins._a0_connector.helpers.browser_bridge_legacy_retirement import get_legacy_retirement, LegacyRetirementDenied


class BlockRetiredLegacyBrowserTool(Extension):
    def execute(self, data: dict, **kwargs):
        args = data.get("args", ())
        named = data.get("kwargs", {})
        name = named.get("name", args[1] if isinstance(args, tuple) and len(args) > 1 else None)
        if name == "chrome_bridge" and get_legacy_retirement().blocked():
            data["exception"] = LegacyRetirementDenied("legacy_bridge_retired")
