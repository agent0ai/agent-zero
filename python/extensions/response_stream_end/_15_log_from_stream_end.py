import asyncio
import math

from agent import LoopData
from python.extensions.before_main_llm_call._10_log_for_stream import (
    build_default_heading,
    build_heading,
)
from python.helpers import log, persist_chat, tokens
from python.helpers.extension import Extension
from python.helpers.log import LogItem


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
