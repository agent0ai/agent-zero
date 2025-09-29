from python.helpers.api import ApiHandler, Request, Response
from python.helpers import model_groups


class ModelGroupDelete(ApiHandler):
    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        name = input.get('name')
        if not name:
            return Response(response='{"error":"name required"}', status=400, mimetype='application/json')
        data = model_groups.delete_group(name)
        return {"status": "ok", "data": data}
