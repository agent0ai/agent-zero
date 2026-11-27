from helpers import socket_handlers


class PluginsList(socket_handlers.JsonApiHandler):
    api_module = "api.plugins_list"
    api_class = "PluginsList"
