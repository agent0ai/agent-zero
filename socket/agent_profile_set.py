from helpers import socket_handlers


class SetAgentProfile(socket_handlers.JsonApiHandler):
    api_module = "api.agent_profile_set"
    api_class = "SetAgentProfile"
    context_field = "context_id"
