from helpers.extension import Extension


class SubordinateStep(Extension):
    def execute(self, ctx: dict | None = None, **kwargs) -> None:
        if not isinstance(ctx, dict) or ctx.get("tool_name") != "call_subordinate":
            return
        args = ctx.get("tool_args")
        if not isinstance(args, dict):
            return
        profile = args.get("profile")
        if isinstance(profile, str) and profile.strip():
            ctx["step"] = f"Calling subordinate {profile.strip()} agent"
        else:
            ctx["step"] = "Calling subordinate agent"
