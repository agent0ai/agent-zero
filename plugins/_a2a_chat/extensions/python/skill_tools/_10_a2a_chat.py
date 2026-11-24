from helpers.extension import Extension
from helpers.skill_tools import SkillTool


def _a2a_chat(**kwargs):
    from plugins._a2a_chat.helpers.chat_handler import A2AChatTool

    return A2AChatTool(**kwargs)


_BINDING = SkillTool("_a2a_chat", "a2a-chat", _a2a_chat)


class RegisterA2AChat(Extension):
    def execute(self, bindings: dict, **kwargs):
        bindings["a2a_chat"] = _BINDING
