from helpers import files
from helpers.extension import Extension
from plugins._browser.helpers.skill_access import saved_tool_access_allows_browser


class GateBrowserSkills(Extension):
    def execute(self, data: dict, **kwargs):
        if not self.agent or not isinstance(data.get("result"), list):
            return

        root = files.get_abs_path("plugins", "_browser", "skills")
        if root in data["result"] and not saved_tool_access_allows_browser(self.agent):
            data["result"] = [path for path in data["result"] if path != root]
