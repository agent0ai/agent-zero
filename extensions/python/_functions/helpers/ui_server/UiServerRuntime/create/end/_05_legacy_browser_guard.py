from helpers.extension import Extension


class LegacyBrowserGuard(Extension):
    def execute(self, data: dict, **kwargs):
        if data.get("exception") is not None:
            return
        from plugins._a0_connector.helpers.browser_bridge_legacy_retirement import install_legacy_retirement_guard

        install_legacy_retirement_guard(data["result"].webapp)
