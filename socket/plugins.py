from helpers import socket_handlers


class Plugins(socket_handlers.JsonApiHandler):
    api_module = "api.plugins"
    api_class = "Plugins"
