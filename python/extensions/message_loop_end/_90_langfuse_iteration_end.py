from python.helpers.extension import Extension
from agent import LoopData


class LangfuseIterationEnd(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        if not loop_data.params_persistent.get("lf_sampled"):
            return

        # End any dangling utility generation
        utility_gen = loop_data.params_temporary.get("lf_utility_gen")
        if utility_gen:
            try:
                utility_gen.end()
            except Exception:
                pass

        # End the iteration span
        span = loop_data.params_temporary.get("lf_iteration_span")
        if span:
            try:
                span.end()
            except Exception:
                pass
