from helpers import socket_handlers


class CreateChat(socket_handlers.JsonApiHandler):
    api_module = "api.chat_create"
    api_class = "CreateChat"
