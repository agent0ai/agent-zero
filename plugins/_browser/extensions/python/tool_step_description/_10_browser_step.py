from helpers.extension import Extension
from plugins._browser.helpers.browser_handler import Browser


class BrowserStep(Extension):
    def execute(self, ctx: dict | None = None, **kwargs) -> None:
        if not isinstance(ctx, dict) or ctx.get("tool_name") != "browser":
            return
        args = ctx.get("tool_args")
        if not isinstance(args, dict):
            return
        action = str(args.get("action") or "").strip().lower()
        action = Browser._HEADING_ALIASES.get(action, action)
        if action != "evaluate":
            return
        ctx["step"] = Browser._HEADING_VERBS.get(action)
