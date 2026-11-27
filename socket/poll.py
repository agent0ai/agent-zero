from helpers import socket_handlers


class Poll(socket_handlers.JsonApiHandler):
    api_module = "api.poll"
    api_class = "Poll"

    def validate(self, input: dict):
        if input.get("context"):
            socket_handlers.require_context(input, "context")
