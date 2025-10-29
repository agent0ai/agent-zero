from python.helpers.api import ApiHandler, Input, Output, Request, Response
from python.helpers import projects


class Projects(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        action = input.get("action", "")

        try:
            if action == "list-active":
                data = self.get_active_projects_list()
            elif action == "list-archive":
                data = self.get_archived_projects_list()
            elif action == "load":
                data = self.load_project(input.get("path", None))
            elif action == "create":
                data = self.create_project(input.get("project", None))
            elif action == "update":
                data = self.update_project(input.get("project", None))
            elif action == "delete":
                data = self.delete_project(input.get("path", None))
            elif action == "activate":
                data = self.activate_project(input.get("context_id", None), input.get("path", None))
            elif action == "deactivate":
                data = self.deactivate_project(input.get("context_id", None))
            else:
                raise Exception("Invalid action")

            return {
                "ok": True,
                "data": data,
            }
        except Exception as e:
            return {
                "ok": False,
                "error": str(e),
            }

    def get_active_projects_list(self):
        return projects.get_active_projects_list()

    def get_archived_projects_list(self):
        return projects.get_archived_projects_list()

    def create_project(self, project: dict|None):
        if project is None:
            raise Exception("Project data is required")
        data = projects.BasicProjectData(**project)
        path = projects.create_project(project["name"], data)
        return projects.load_edit_project_data(path)

    def load_project(self, path: str|None):
        if path is None:
            raise Exception("Project path is required")
        return projects.load_edit_project_data(path)

    def update_project(self, project: dict|None):
        if project is None:
            raise Exception("Project data is required")
        data = projects.BasicProjectData(**project)
        path = projects.update_project(project["path"], data)
        return projects.load_edit_project_data(path)

    def delete_project(self, path: str|None):
        if path is None:
            raise Exception("Project path is required")
        return projects.delete_project(path)

    def activate_project(self, context_id: str|None, path: str|None):
        if context_id is None:
            raise Exception("Context ID is required")
        if path is None:
            raise Exception("Project path is required") 
        return projects.activate_project(context_id, path)

    def deactivate_project(self, context_id: str|None):
        if context_id is None:
            raise Exception("Context ID is required")
        return projects.deactivate_project(context_id)
