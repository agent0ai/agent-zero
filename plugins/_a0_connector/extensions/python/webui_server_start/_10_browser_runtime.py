from helpers.extension import Extension
from plugins._a0_connector.helpers.browser_bridge_runtime_owner import (
    install_configured_browser_runtime,
    retire_configured_browser_runtime,
)


class BrowserRuntime(Extension):
    def execute(self, runtime, shutdown, **kwargs):
        if install_configured_browser_runtime(runtime.ws_manager):
            shutdown.push_async_callback(
                retire_configured_browser_runtime, manager=runtime.ws_manager,
            )
