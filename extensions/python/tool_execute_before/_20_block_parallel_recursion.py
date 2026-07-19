from helpers.extension import Extension
from helpers.errors import RepairableException
from helpers import parallel_tools


class BlockParallelRecursion(Extension):
    async def execute(self, tool_name: str = "", **kwargs) -> None:
        if tool_name != "parallel":
            return
        if not parallel_tools.is_parallel_worker(self.agent):
            return
        raise RepairableException(
            "The `parallel` tool cannot be used inside a parallel worker. "
            "Finish the current worker task sequentially and return its result."
        )
