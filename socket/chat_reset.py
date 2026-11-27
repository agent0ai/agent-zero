from helpers import socket_handlers


class Reset(socket_handlers.JsonApiHandler):
    api_module = "api.chat_reset"
    api_class = "Reset"
    context_field = "context"
