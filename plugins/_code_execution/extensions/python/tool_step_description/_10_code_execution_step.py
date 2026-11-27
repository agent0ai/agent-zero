from helpers.extension import Extension


class CodeExecutionStep(Extension):
    def execute(self, ctx: dict | None = None, **kwargs) -> None:
        if not isinstance(ctx, dict) or ctx.get("tool_name") != "code_execution_tool":
            return
        args = ctx.get("tool_args")
        if not isinstance(args, dict) or "runtime" not in args:
            return
        code = args.get("code")
        if isinstance(code, str):
            ctx["step"] = "Writing code..."
        runtime = args["runtime"]
        if runtime == "python":
            ctx["step"] = "Writing Python code..."
        elif runtime == "nodejs":
            ctx["step"] = "Writing Node.js code..."
        elif runtime == "terminal":
            ctx["step"] = "Writing terminal command..."
