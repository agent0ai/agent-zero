from helpers.extension import Extension
from agent import LoopData
from helpers import parallel_tools


class IncludeParallelJobs(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        if not self.agent:
            return

        extras = await parallel_tools.build_parallel_jobs_extras(self.agent)
        if extras:
            loop_data.extras_temporary["parallel_jobs"] = extras
