from python.helpers.api import ApiHandler, Request, Response
from python.helpers import plugins


class PluginsResolve(ApiHandler):
    """
    API handler for resolving plugin manifests.
    Accepts a plugin ID or list of IDs and returns normalized manifest(s) with URLs and props.
    
    Single ID: {"id": "example"} -> {"ok": True, "data": {...}}
    Multiple IDs: {"ids": ["example", "another"]} -> {"ok": True, "data": [{...}, {...}]}
    """

    @classmethod
    def get_methods(cls):
        return ["POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        # Support both single ID and array of IDs
        plugin_id = input.get("id")
        plugin_ids = input.get("ids")
        
        # Batch mode: array of IDs
        if plugin_ids:
            if not isinstance(plugin_ids, list):
                return {"ok": False, "error": "ids must be an array"}
            
            results = []
            for pid in plugin_ids:
                plugin = plugins.find_plugin(pid)
                if plugin:
                    results.append(plugins.build_plugin_response_data(plugin))
                else:
                    results.append({
                        "id": pid,
                        "error": f"Plugin '{pid}' not found or invalid manifest"
                    })
            
            return {"ok": True, "data": results}
        
        # Single mode: one ID
        elif plugin_id:
            plugin = plugins.find_plugin(plugin_id)
            if not plugin:
                return {"ok": False, "error": f"Plugin '{plugin_id}' not found or invalid manifest"}
            
            return {"ok": True, "data": plugins.build_plugin_response_data(plugin)}
        
        else:
            return {"ok": False, "error": "Missing plugin ID or IDs"}
