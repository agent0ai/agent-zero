from agent import AgentContext, AgentContextType
from helpers import persist_chat, projects
from helpers.api import ApiHandler, Input, Output, Request, Response
from helpers.state_monitor_integration import mark_dirty_all
from helpers.task_scheduler import TaskScheduler


def parent_id(context):
    return context.get_output_data("parent_context_id") or context.get_data(
        "_parallel_parent_context_id"
    )


def chat_family(context):
    """Keep visible children and background parallel workers with their root."""
    contexts = {item.id: item for item in AgentContext.all()}
    seen = set()
    while parent_id(context) in contexts:
        if context.id in seen:
            raise ValueError("Invalid chat parent cycle")
        seen.add(context.id)
        context = contexts[parent_id(context)]
    family = [context]
    seen = {context.id}
    children = {}
    for item in contexts.values():
        children.setdefault(parent_id(item), []).append(item)
    for item in family:
        for child in children.get(item.id, []):
            if child.id not in seen:
                seen.add(child.id)
                family.append(child)
    return family


class MoveChat(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        context_id, project_name = input.get("context_id"), input.get("project_name")
        if not isinstance(context_id, str) or not isinstance(project_name, str):
            return Response("context_id and project_name must be strings", 400)
        with self.thread_lock:
            context = AgentContext.get(context_id)
            if context is None:
                return Response("Chat not found", 404)
            try:
                if project_name:
                    projects.validate_project_name(project_name)
                    projects.load_basic_project_data(project_name)
                family = chat_family(context)
            except (ValueError, FileNotFoundError):
                return Response("Invalid project or chat family", 400)

            scheduler = TaskScheduler.get()
            if family[0].type != AgentContextType.USER or any(
                scheduler.get_task_by_uuid(item.id) for item in family
            ):
                return Response("Scheduled tasks keep their configured project", 409)
            if any(item.is_running() for item in family):
                return Response("Stop the chat and its parallel calls before moving it", 409)

            # Restore project and profile state if any family member fails to save.
            previous = [(item, dict(item.data), dict(item.output_data), item.config) for item in family]
            try:
                for item in family:
                    if project_name:
                        projects.activate_project(item.id, project_name, mark_dirty=False)
                    else:
                        projects.deactivate_project(item.id, mark_dirty=False)
            except Exception:
                for item, data, output_data, config in previous:
                    item.data, item.output_data, item.config = data, output_data, config
                    item.agent0.config = config
                for item in family:
                    persist_chat.save_tmp_chat(item)
                return Response("Could not move the chat. Please retry.", 500)
            finally:
                mark_dirty_all(reason="plugins._sidebar_folders.move_chat")

            return {
                "ok": True,
                "context_ids": [item.id for item in family],
                "project": family[0].get_output_data(projects.CONTEXT_DATA_KEY_PROJECT),
            }
