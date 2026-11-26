from helpers.api import ApiHandler, Input, Output, Request, Response


from helpers import settings, projects, guids, login, team_access
from helpers.state_monitor_integration import mark_dirty_all
from helpers.team_store import ADMIN_ACTOR_ID
from agent import AgentContext


class CreateChat(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        if scope := team_access.request_scope():
            name = input.get("project_name")
            if not isinstance(name, str) or not name:
                return Response("Select a project before starting a chat.", 400)
            if name not in scope.project_ids:
                return Response("Project access denied.", 403)

            return self._project_draft(scope, name, input.get("preset_name"))

        # An explicit project choice takes precedence over chat inheritance.
        project_name = input.get("project_name")
        if "project_name" in input:
            if not isinstance(project_name, str):
                return Response("project_name must be a string", 400)
            if project_name:
                try:
                    projects.validate_project_name(project_name)
                    projects.load_basic_project_data(project_name)
                except (ValueError, FileNotFoundError):
                    return Response("Project not found", 400)
        current_ctxid = input.get("current_context", "") # current context id
        current_context = AgentContext.get(current_ctxid) if isinstance(current_ctxid, str) else None
        inherited_project = None
        if "project_name" not in input and current_context and settings.get_settings().get("chat_inherit_project", True):
            inherited_project = projects.get_context_project_name(current_context)
        if login.team_mode_enabled() and (team_project := project_name or inherited_project):
            try:
                project_id = team_access.register_project(team_project)
            except (OSError, ValueError):
                return Response("Project not found", 400)
            scope = team_access.MemberScope(ADMIN_ACTOR_ID, {team_project: project_id})
            return self._project_draft(scope, team_project, input.get("preset_name"))

        new_ctxid = input.get("new_context", guids.generate_id()) # given or new guid
        if team_access.is_team_chat_id(new_ctxid):
            return Response("Choose a new chat ID.", 403)

        # get/create new context
        new_context = self.use_context(new_ctxid)

        # copy selected data from current to new context
        if "project_name" in input:
            if project_name:
                projects.activate_project(new_context.id, project_name, mark_dirty=False)
            else:
                projects.deactivate_project(new_context.id, mark_dirty=False)
        elif inherited_project:
            new_context.set_data(projects.CONTEXT_DATA_KEY_PROJECT, inherited_project)
            output_project = current_context.get_output_data(projects.CONTEXT_DATA_KEY_PROJECT)
            if output_project:
                new_context.set_output_data(projects.CONTEXT_DATA_KEY_PROJECT, output_project)

        projects.reconcile_agent_profile(
            new_context, projects.get_context_project_name(new_context)
        )

        # copy model override from current context (only if override is allowed)
        if current_context:
            model_override = current_context.get_data("chat_model_override")
            if model_override:
                from plugins._model_config.helpers.model_config import is_chat_override_allowed
                if is_chat_override_allowed(new_context.agent0):
                    new_context.set_data("chat_model_override", model_override)

        # New context should appear in other tabs' chat lists via state_push.
        mark_dirty_all(reason="api.chat_create.CreateChat")

        return {
            "ok": True,
            "ctxid": new_context.id,
            "message": "Context created.",
        }

    def _project_draft(self, scope: team_access.MemberScope, name: str, preset_name: object) -> Output:
        preset = None
        if preset_name:
            from plugins._model_config.helpers.model_config import get_preset_by_name

            if not isinstance(preset_name, str) or not (preset := get_preset_by_name(preset_name)):
                return Response("Select a configured model preset.", 400)
        with self.thread_lock:
            team_access.prune_drafts()
            context = self.use_context(guids.generate_id())
            team_access.bind_chat(context, scope, name, draft=True)
            if preset:
                context.set_data("chat_model_override", {"preset_name": preset["name"]})
        return {"ok": True, "ctxid": context.id, "draft": True, "message": "Context created."}
