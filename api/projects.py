from helpers.api import ApiHandler, Input, Output, Request, Response
from helpers import login, projects, team_access, team_projects
from helpers.notification import NotificationManager, NotificationType, NotificationPriority


class Projects(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        action = input.get("action", "")
        if scope := team_access.request_scope():
            return self.process_member(action, input, scope)

        ctxid = input.get("context_id", None)
        if action in ("activate", "deactivate") and team_access.is_team_chat_id(ctxid):
            return Response("Shared chat ownership is fixed.", 403)

        if ctxid:
            _context = self.use_context(ctxid)

        try:
            if action == "list":
                data = self.get_active_projects_list()
            elif action == "list_options":
                data = self.get_active_projects_options()
            elif action == "load":
                data = self.load_project(input.get("name", None))
            elif action == "create":
                data = self.create_project(input.get("project", None))
            elif action == "clone":
                data = self.clone_project(input.get("project", None))
            elif action == "update":
                data = self.update_project(input.get("project", None))
            elif action == "delete":
                data = self.delete_project(input.get("name", None))
            elif action == "activate":
                data = self.activate_project(ctxid, input.get("name", None))
            elif action == "deactivate":
                data = self.deactivate_project(ctxid)
            elif action == "file_structure":
                data = self.get_file_structure(input.get("name", None), input.get("settings"))
            else:
                raise Exception("Invalid action")

            return {
                "ok": True,
                "data": data,
            }
        except team_projects.RevisionConflict as error:
            return Response(str(error), 409)
        except Exception as e:
            return {
                "ok": False,
                "error": str(e),
            }

    def process_member(self, action, input, scope):
        if action in ("list", "list_options"):
            authorized = []
            for name in sorted(scope.project_ids):
                try:
                    data = projects.load_basic_project_data(name)
                except (OSError, ValueError):
                    continue
                authorized.append({"name": name, **{field: data[field] for field in ("title", "description", "color")}})
            data = [self.project_option(item) for item in authorized] if action == "list_options" else authorized
            return {"ok": True, "data": data}
        if action not in ("load", "update"):
            return Response("Project action forbidden.", 403)
        raw = input if action == "load" else input.get("project")
        name = raw.get("name") if isinstance(raw, dict) else None
        if not isinstance(name, str) or name not in scope.project_ids:
            return Response("Project access denied.", 403)
        try:
            with team_projects.project_lock(name, scope) as project_id:
                if action == "load":
                    data = team_projects.load_member_settings(name)
                else:
                    with team_projects.activity("project.settings.save", scope.account_id, project_id):
                        data = team_projects.save_member_settings(name, raw)
        except PermissionError:
            return Response("Project access denied.", 403)
        except team_projects.RevisionConflict as error:
            return Response(str(error), 409)
        except ValueError as error:
            return Response(str(error), 400)
        except OSError:
            return Response("The project settings could not be accessed.", 500)
        return {"ok": True, "data": data}

    def get_active_projects_list(self):
        return projects.get_active_projects_list()

    def get_active_projects_options(self):
        items = projects.get_active_projects_list() or []
        return [self.project_option(item) for item in items if item.get("name")]

    @staticmethod
    def project_option(item):
        return {"key": item["name"], "label": item.get("title") or item["name"]}

    def create_project(self, project: dict|None):
        if project is None:
            raise Exception("Project data is required")
        data = projects.BasicProjectData(**project)
        name = projects.create_project(project["name"], data)
        return projects.load_edit_project_data(name)

    def clone_project(self, project: dict|None):
        if project is None:
            raise Exception("Project data is required")
        git_url = project.get("git_url", "")
        git_token = project.get("git_token", "")
        if not git_url:
            raise Exception("Git URL is required")
        
        # Progress notification
        notification = NotificationManager.send_notification(
            NotificationType.PROGRESS,
            NotificationPriority.NORMAL,
            f"Cloning repository...",
            "Git Clone",
            display_time=999,
            group="git_clone"
        )
        
        try:
            data = projects.BasicProjectData(**project)
            name = projects.clone_git_project(project["name"], git_url, git_token, data)
            
            # Success notification
            NotificationManager.send_notification(
                NotificationType.SUCCESS,
                NotificationPriority.NORMAL,
                f"Repository cloned successfully",
                "Git Clone",
                display_time=3,
                group="git_clone"
            )
            return projects.load_edit_project_data(name)
        except Exception as e:
            # Error notification
            NotificationManager.send_notification(
                NotificationType.ERROR,
                NotificationPriority.HIGH,
                f"Clone failed: {str(e)}",
                "Git Clone",
                display_time=5,
                group="git_clone"
            )
            raise

    def load_project(self, name: str|None):
        if name is None:
            raise Exception("Project name is required")
        if login.team_mode_enabled() and team_access.bound_project_id(name):
            with team_projects.project_lock(name, None):
                return {**projects.load_edit_project_data(name), "revision": team_projects.header_revision(name)}
        return projects.load_edit_project_data(name)

    def update_project(self, project: dict|None):
        if project is None:
            raise Exception("Project data is required")
        data = projects.EditProjectData(**{key: value for key, value in project.items() if key != "revision"})
        name = project["name"]
        if login.team_mode_enabled() and team_access.bound_project_id(name):
            with team_projects.project_lock(name, None) as project_id, team_projects.activity("project.settings.save", "admin", project_id):
                team_projects.require_revision(project.get("revision"), team_projects.header_revision(name))
                projects.update_project(name, data, atomic_header=True)
                return self.load_project(name)
        name = projects.update_project(project["name"], data)
        return projects.load_edit_project_data(name)

    def delete_project(self, name: str|None):
        if name is None:
            raise Exception("Project name is required")
        return projects.delete_project(name)

    def activate_project(self, context_id: str|None, name: str|None):
        if not context_id:
            raise Exception("Context ID is required")
        if not name:
            raise Exception("Project name is required") 
        return projects.activate_project(context_id, name)

    def deactivate_project(self, context_id: str|None):
        if not context_id:
            raise Exception("Context ID is required")
        return projects.deactivate_project(context_id)

    def get_file_structure(self, name: str|None, settings: dict|None):
        if not name:
            raise Exception("Project name is required")
        # project data
        basic_data = projects.load_basic_project_data(name)
        # override file structure settings
        if settings:
            basic_data["file_structure"] = settings # type: ignore
        # get structure
        return projects.get_file_structure(name, basic_data)
