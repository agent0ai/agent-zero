from helpers import socket_handlers


class Projects(socket_handlers.JsonApiHandler):
    api_module = "api.projects"
    api_class = "Projects"

    def validate(self, input: dict):
        if input.get("context_id") or input.get("action") in ("activate", "deactivate"):
            socket_handlers.require_context(input, "context_id")
