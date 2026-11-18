from helpers import socket_handlers


class Agents(socket_handlers.JsonApiHandler):
    api_module = "api.agents"
    api_class = "Agents"
