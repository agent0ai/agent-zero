from helpers.extension import Extension
from plugins._text_editor.helpers.log import ACTION_VERBS


class TextEditorStep(Extension):
    def execute(self, ctx: dict | None = None, **kwargs) -> None:
        if not isinstance(ctx, dict) or ctx.get("tool_name") != "text_editor":
            return
        args = ctx.get("tool_args")
        if not isinstance(args, dict):
            return
        action = str(args.get("action") or "").strip().lower().replace("-", "_")
        verb = ACTION_VERBS.get(action)
        if not verb:
            return
        ctx["step"] = f"{verb} file"
