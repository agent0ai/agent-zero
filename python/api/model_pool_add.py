from python.helpers.api import ApiHandler, Request, Response
from python.helpers import model_groups


class ModelPoolAdd(ApiHandler):
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
        api_base = input.get('api_base', '')
        kwargs = input.get('kwargs', {})
        if not model_type:
            return Response(response='{"error":"type required"}', status=400, mimetype='application/json')
        model_type = model_type.lower()
        if model_type == 'util':
            model_type = 'utility'
        if model_type not in ('chat', 'utility'):
            return Response(response='{"error":"type must be chat or utility"}', status=400, mimetype='application/json')
        if not provider or not name:
            return Response(response='{"error":"provider and name required"}', status=400, mimetype='application/json')
        data = model_groups.add_model_to_pool(model_type, provider, name, api_base, kwargs)
        return {"status": "ok", "data": data}
