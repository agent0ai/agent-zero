from python.helpers.api import ApiHandler, Request, Response
from python.helpers import plugins


class PluginsList(ApiHandler):
    """
    API handler for listing all available plugins.
    Returns a list of plugin manifests.
    """

    @classmethod
    def get_methods(cls):
        return ["GET", "POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        # Get all available plugins
        plugin_list = plugins.list_plugins()
        
        # Serialize plugin objects using helper
        data = [plugins.build_plugin_response_data(p) for p in plugin_list]
        
        return {"ok": True, "data": data}
