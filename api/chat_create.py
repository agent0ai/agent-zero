from helpers.api import ApiHandler, Input, Output, Request, Response


from helpers import settings, projects, guids
from agent import AgentContext


class CreateChat(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        current_ctxid = input.get("current_context", "") # current context id
        new_ctxid = input.get("new_context", guids.generate_id()) # given or new guid

        # context instance - get or create
        current_context = AgentContext.get(current_ctxid)

        # get/create new context
        new_context = self.use_context(new_ctxid)

        # copy selected data from current to new context
        if current_context and settings.get_settings().get("chat_inherit_project", True):
            current_data_1 = current_context.get_data(projects.CONTEXT_DATA_KEY_PROJECT)
            if current_data_1:
                new_context.set_data(projects.CONTEXT_DATA_KEY_PROJECT, current_data_1)
            current_data_2 = current_context.get_output_data(projects.CONTEXT_DATA_KEY_PROJECT)
            if current_data_2:
                new_context.set_output_data(projects.CONTEXT_DATA_KEY_PROJECT, current_data_2)

        # copy model override from current context (only if override is allowed)
        if current_context:
            model_override = current_context.get_data("chat_model_override")
            if model_override:
                from plugins._model_config.helpers.model_config import is_chat_override_allowed
                if is_chat_override_allowed(new_context.agent0):
                    new_context.set_data("chat_model_override", model_override)

        # New context should appear in other tabs' chat lists via state_push.
        from helpers.state_monitor_integration import mark_dirty_all
        mark_dirty_all(reason="api.chat_create.CreateChat")

        return {
            "ok": True,
            "ctxid": new_context.id,
            "message": "Context created.",
        }
