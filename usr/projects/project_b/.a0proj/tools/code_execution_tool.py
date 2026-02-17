from python.tools.code_execution_tool import CodeExecution as BaseCodeExecution, make_dir
from python.helpers import files, runtime


class CodeExecution(BaseCodeExecution):
    """Override cwd to use benchmark run_dir for subordinate agents."""

    async def ensure_cwd(self) -> str | None:
        # During a benchmark run, subordinates work in the task's run_dir
        state = self.agent.context.get_data("benchmark_project_state")
        if state and self.agent.number > 0:
            run_dir = state.get("run_dir")
            if run_dir:
                normalized = files.normalize_a0_path(run_dir)
                await runtime.call_development_function(make_dir, normalized)
                return normalized

        return await super().ensure_cwd()
