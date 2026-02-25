from python.helpers.extension import Extension
from python.helpers.tool import Response


class LangfuseToolSpanEnd(Extension):

    async def execute(self, response: Response | None = None, tool_name: str = "", **kwargs):
        loop_data = self.agent.loop_data
        if not loop_data or not loop_data.params_persistent.get("lf_sampled"):
            return

        span = loop_data.params_temporary.get("lf_tool_span")
        if not span:
            return

        output = ""
        if response:
            output = str(response.message)[:2000] if response.message else ""

        try:
            span.update(output=output)
            span.end()
        except Exception:
            pass
