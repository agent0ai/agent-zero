from python.helpers.api import ApiHandler, Request, Response
from python.helpers import model_groups


class ModelPoolRemove(ApiHandler):
    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        model_type = input.get('type')
        provider = input.get('provider')
        name = input.get('name')
        if not model_type or not provider or not name:
            return Response(response='{"error":"type/provider/name required"}', status=400, mimetype='application/json')
        model_type = model_type.lower()
        if model_type == 'util':
            model_type = 'utility'
        if model_type not in ('chat', 'utility'):
            return Response(response='{"error":"type must be chat or utility"}', status=400, mimetype='application/json')
        data = model_groups.remove_model_from_pool(model_type, provider, name)
        return {"status": "ok", "data": data}
