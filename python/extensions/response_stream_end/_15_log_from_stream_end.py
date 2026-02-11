from agent import LoopData
from python.helpers.extension import Extension


class LogFromStream(Extension):
    async def execute(
        self,
        loop_data: LoopData = LoopData(),
        text: str = "",
        parsed: dict = {},
        **kwargs,
    ):
        # get log item from loop data temporary params
        log_item = loop_data.params_temporary["log_item_generating"]
        if log_item is None:
            return

        # remove step parameter when done
        if log_item.kvps is not None and "step" in log_item.kvps:
            del log_item.kvps["step"]

        # update the log item
        log_item.update(kvps=log_item.kvps)
