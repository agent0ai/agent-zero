from helpers.extension import Extension
from helpers.skill_tools import SkillTool


def _browser(**kwargs):
    from plugins._browser.helpers.browser_handler import Browser

    return Browser(**kwargs)


_BINDING = SkillTool("_browser", "browser-automation", _browser)


class RegisterBrowser(Extension):
    def execute(self, bindings: dict, **kwargs):
        bindings["browser"] = _BINDING
