from python.helpers.api import ApiHandler, Request, Response
from python.helpers import model_groups, settings as settings_helper
import json


class ModelGroupSelect(ApiHandler):
    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        grp = input.get('group')
        if not grp:
            return Response(response='{"error":"group field required"}', status=400, mimetype='application/json')

        g = model_groups.get_group(grp)
        if not g:
            return Response(response='{"error":"group not found"}', status=404, mimetype='application/json')

        # map group to settings delta
        delta = {}
        chat = g.get('chat', {})
        util = g.get('util', {})

        # Attempt to fill missing api_base from pool entries if needed
        try:
            mg_all = model_groups.get_all()
            chat_pool = mg_all.get('chat_models', [])
            util_pool = mg_all.get('utility_models', [])
        except Exception:
            chat_pool = []
            util_pool = []

        def find_api_base(pool, provider, name):
            if not provider or not name:
                return ''
            p_low = (provider or '').lower()
            n_low = (name or '').lower()
            for m in pool:
                try:
                    if (m.get('provider') or '').lower() == p_low and (m.get('name') or '').lower() == n_low:
                        return m.get('api_base', '') or ''
                except Exception:
                    continue
            return ''

        if chat:
            chat_provider = chat.get('provider', '')
            chat_name = chat.get('name', '')
            chat_api = chat.get('api_base', '') or find_api_base(chat_pool, chat_provider, chat_name)
            delta['chat_model_provider'] = chat_provider
            delta['chat_model_name'] = chat_name
            delta['chat_model_api_base'] = chat_api
            delta['chat_model_kwargs'] = chat.get('kwargs', {})
        if util:
            util_provider = util.get('provider', '')
            util_name = util.get('name', '')
            util_api = util.get('api_base', '') or find_api_base(util_pool, util_provider, util_name)
            delta['util_model_provider'] = util_provider
            delta['util_model_name'] = util_name
            delta['util_model_api_base'] = util_api
            delta['util_model_kwargs'] = util.get('kwargs', {})

        # apply settings runtime and capture errors
        applied = False
        error_msg = None
        try:
            settings_helper.set_settings_delta(delta, apply=True)
            applied = True
        except Exception as e:
            error_msg = str(e)

        # mark active group in model_groups persistence (non-fatal)
        try:
            model_groups.set_active(grp)
        except Exception:
            # ignore persistence failures
            pass

        result = {"status": "ok" if applied else "error", "applied": applied, "active": grp}
        if error_msg:
            result["error"] = error_msg

        if not applied:
            return Response(response=json.dumps(result), status=500, mimetype='application/json')

        return result

