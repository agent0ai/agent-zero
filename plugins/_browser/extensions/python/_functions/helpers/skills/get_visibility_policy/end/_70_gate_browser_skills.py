from helpers.extension import Extension
from helpers.skills import normalize_visibility_policy
from plugins._browser.helpers.skill_access import saved_tool_access_allows_browser


class GateBrowserSkillOverrides(Extension):
    def execute(self, data: dict, **kwargs):
        policy = data["result"]
        if not self.agent or not isinstance(policy, dict) or saved_tool_access_allows_browser(self.agent):
            return
        if policy["mode"] != "custom":
            policy = normalize_visibility_policy(None)
        data["result"] = {
            **policy,
            "mode": "custom",
            "blocked": [
                *policy["blocked"],
                "browser-automation",
                "browser-extension-control",
                "browser-form-workflows",
            ],
        }
