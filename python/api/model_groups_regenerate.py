from python.helpers.api import ApiHandler, Request, Response
from python.helpers import model_groups, settings as settings_helper


class ModelGroupsRegenerate(ApiHandler):
    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        force = bool(input.get('force'))
        # load existing model_groups and current settings
        mg = model_groups.get_all()
        s = settings_helper.get_settings()

        # Helper: check if group/default chat/util match current settings
        def _is_default_matching_settings(mg_obj, settings_obj):
            try:
                groups = mg_obj.get('groups', {})
                default_name = mg_obj.get('default')
                if not default_name or default_name not in groups:
                    return False
                g = groups[default_name]
                chat = g.get('chat', {}) or {}
                util = g.get('util', {}) or {}
                # compare provider and name
                if (chat.get('provider') or '') != (settings_obj.get('chat_model_provider') or ''):
                    return False
                if (chat.get('name') or '') != (settings_obj.get('chat_model_name') or ''):
                    return False
                if (util.get('provider') or '') != (settings_obj.get('util_model_provider') or ''):
                    return False
                if (util.get('name') or '') != (settings_obj.get('util_model_name') or ''):
                    return False
                return True
            except Exception:
                return False

        if force:
            data = model_groups.create_default_from_settings()
            return {"status": "ok", "data": data}

        # If default missing or not matching current settings or default's chat/util empty -> regenerate
        default_missing = not (mg.get('groups') and mg.get('default'))
        default_mismatch = not _is_default_matching_settings(mg, s)
        if default_missing or default_mismatch:
            data = model_groups.create_default_from_settings()
            return {"status": "ok", "data": data, "reason": "regenerated"}

        return {"status": "skipped", "reason": "default up-to-date"}
