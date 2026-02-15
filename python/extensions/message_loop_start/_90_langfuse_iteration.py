from python.helpers.extension import Extension
from agent import LoopData


class LangfuseIterationStart(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        if not loop_data.params_persistent.get("lf_sampled"):
            return

        trace = loop_data.params_persistent.get("lf_trace")
        if not trace:
            return

        span = trace.start_span(
            name=f"iteration-{loop_data.iteration}",
            metadata={"iteration": loop_data.iteration},
        )
        loop_data.params_temporary["lf_iteration_span"] = span
