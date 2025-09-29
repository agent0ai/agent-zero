from python.helpers.api import ApiHandler, Request, Response
from python.helpers import model_groups


class ModelGroupsManage(ApiHandler):
    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        action = input.get('action')
        if not action:
            return Response(response='{"error":"action required"}', status=400, mimetype='application/json')

        try:
            if action == 'create_group':
                name = str(input.get('name') or '')
                chat = input.get('chat') or {}
                util = input.get('util') or {}
                data = model_groups.create_group(name, chat, util)
                return data
            if action == 'update_group':
                name = str(input.get('name') or '')
                chat = input.get('chat') if 'chat' in input else None
                util = input.get('util') if 'util' in input else None
                data = model_groups.update_group(name, chat, util)
                return data
            if action == 'delete_group':
                name = str(input.get('name') or '')
                data = model_groups.delete_group(name)
                return data
            if action == 'add_model':
                mtype = str(input.get('type') or '')
                provider = str(input.get('provider') or '')
                name = str(input.get('model') or '')
                api_base = str(input.get('api_base') or '')
                kwargs = input.get('kwargs', {}) or {}
                data = model_groups.add_model_to_pool(mtype, provider, name, api_base, kwargs)
                return data
            if action == 'remove_model':
                mtype = str(input.get('type') or '')
                provider = str(input.get('provider') or '')
                name = str(input.get('model') or '')
                data = model_groups.remove_model_from_pool(mtype, provider, name)
                return data
        except KeyError:
            return Response(response='{"error":"not found"}', status=404, mimetype='application/json')
        except Exception as e:
            return Response(response=f'{{"error":"{str(e)}"}}', status=500, mimetype='application/json')

        return Response(response='{"error":"unknown action"}', status=400, mimetype='application/json')
