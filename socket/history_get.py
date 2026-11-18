from helpers import socket_handlers


class GetHistory(socket_handlers.JsonApiHandler):
    api_module = "api.history_get"
    api_class = "GetHistory"
    context_field = "context"
