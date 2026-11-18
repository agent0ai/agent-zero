from helpers import socket_handlers


class Pause(socket_handlers.JsonApiHandler):
    api_module = "api.pause"
    api_class = "Pause"
    context_field = "context"
