from python.helpers.extension import Extension


class LangfuseToolSpanStart(Extension):

    async def execute(self, tool_name: str = "", tool_args: dict = {}, **kwargs):
        loop_data = self.agent.loop_data
        if not loop_data or not loop_data.params_persistent.get("lf_sampled"):
            return

        parent = loop_data.params_temporary.get("lf_iteration_span")
        if not parent:
            parent = loop_data.params_persistent.get("lf_trace")
        if not parent:
            return

        args_summary = {}
        for k, v in (tool_args or {}).items():
            val_str = str(v)
            args_summary[k] = val_str[:500] if len(val_str) > 500 else val_str

        span = parent.start_span(
            name=f"tool-{tool_name}" if tool_name else "tool-unknown",
            input=args_summary,
            metadata={"tool_name": tool_name},
        )
        loop_data.params_temporary["lf_tool_span"] = span
