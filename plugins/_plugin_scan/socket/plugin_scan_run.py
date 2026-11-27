from helpers import socket_handlers


class PluginScanRun(socket_handlers.JsonApiHandler):
    api_module = "plugins._plugin_scan.api.plugin_scan_run"
    api_class = "PluginScanRun"
