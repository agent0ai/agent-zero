from python.helpers.api import ApiHandler, Request, Response
from python.helpers import model_groups


class ModelGroupUpdate(ApiHandler):
    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        name = input.get('name')
        new_name = input.get('new_name')
        chat = input.get('chat')
        util = input.get('util')
        if not name:
            return Response(response='{"error":"name required"}', status=400, mimetype='application/json')
        try:
            # if renaming requested, perform rename first (validate conflicts)
            if new_name and new_name != name:
                try:
                    model_groups.rename_group(name, new_name)
                except KeyError as e:
                    # rename failed: either original not found or new name exists
                    return Response(response=json_response({'error': str(e)}), status=409, mimetype='application/json')
                name_to_use = new_name
            else:
                name_to_use = name

            # perform update (chat/util may be omitted)
            data = model_groups.update_group(name_to_use, chat if chat is not None else None, util if util is not None else None)
        except KeyError:
            return Response(response='{"error":"group not found"}', status=404, mimetype='application/json')
        return {"status": "ok", "data": data}


def json_response(obj: dict) -> str:
    try:
        import json as _json
        return _json.dumps(obj)
    except Exception:
        return '{"error":"unknown"}'
