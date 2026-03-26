from python.helpers.api import ApiHandler, Request, Response
from python.helpers import plugins


class PluginsResolve(ApiHandler):
    """
    Return all injectable plugin frontend components.
    Each plugin's extensions/frontend/**/*.html files are returned.
    The components themselves declare their injection target via <meta> tags.
    """

    @classmethod
    def get_methods(cls):
        return ["POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        data = plugins.get_frontend_components()
        return {"ok": True, "data": data}
