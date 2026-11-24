from helpers import tool_policy
from helpers.tool_actions import action_policy_id


_BROWSER_TOOL_ID = "plugin:_browser:browser"
# Scope default blocks apply to every action from the former Tool Access catalog.
_LEGACY_ACTION_IDS = frozenset(
    action_policy_id(_BROWSER_TOOL_ID, action)
    for action in (
        "open", "list", "state", "set_active", "navigate", "back", "forward", "reload",
        "content", "detail", "screenshot", "click", "type", "submit", "type_submit",
        "scroll", "evaluate", "cdp", "key_chord", "hover", "double_click", "right_click",
        "drag", "wheel", "keyboard", "clipboard", "set_viewport", "select_option",
        "set_checked", "upload_file", "mouse", "multi", "close", "close_all",
    )
)


def saved_tool_access_allows_browser(agent) -> bool:
    policy = tool_policy.get_policy(agent)
    if policy["mode"] != "custom":
        return True

    if any(
        tool_id == _BROWSER_TOOL_ID or tool_id.startswith(f"{_BROWSER_TOOL_ID}:")
        for tool_id in policy["blocked"]
    ):
        return False

    allowed = policy["allowed"]
    return (
        policy["default"] == "allow"
        or _BROWSER_TOOL_ID in allowed
        or _LEGACY_ACTION_IDS.issubset(allowed)
    )
