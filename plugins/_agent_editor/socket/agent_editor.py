from helpers import socket_handlers


class AgentEditor(socket_handlers.JsonApiHandler):
    api_module = "plugins._agent_editor.api.agent_editor"
    api_class = "AgentEditor"
