from helpers import socket_handlers


class Stop(socket_handlers.JsonApiHandler):
    api_module = "api.stop"
    api_class = "Stop"
    context_field = "context"
