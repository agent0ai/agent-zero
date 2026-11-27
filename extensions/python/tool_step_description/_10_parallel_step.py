import json

from helpers.extension import Extension


class ParallelStep(Extension):
    def execute(self, ctx: dict | None = None, **kwargs) -> None:
        if not isinstance(ctx, dict) or ctx.get("tool_name") != "parallel":
            return
        args = ctx.get("tool_args")
        if not isinstance(args, dict):
            return
        raw_calls = next((args[key] for key in ("tool_calls", "calls", "items") if key in args), None)
        if isinstance(raw_calls, str):
            try:
                raw_calls = json.loads(raw_calls)
            except json.JSONDecodeError:
                return
        if not isinstance(raw_calls, list) or not raw_calls:
            return
        head = ""
        if isinstance(raw_calls[0], dict):
            name = raw_calls[0].get("tool_name") or raw_calls[0].get("tool") or raw_calls[0].get("name")
            if isinstance(name, str) and name:
                head = name.replace("_", " ")
        if not head:
            return
        more = len(raw_calls) - 1
        if more > 0:
            ctx["step"] = f"Using in parallel {head} and {more} more tools"
        else:
            ctx["step"] = f"Using in parallel {head}"
