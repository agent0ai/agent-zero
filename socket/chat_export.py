from helpers import socket_handlers


class ExportChat(socket_handlers.JsonApiHandler):
    api_module = "api.chat_export"
    api_class = "ExportChat"
    context_field = "ctxid"
