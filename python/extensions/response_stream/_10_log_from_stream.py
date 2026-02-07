from python.helpers import persist_chat, tokens
from python.helpers.extension import Extension
from agent import LoopData
import asyncio
from python.helpers.log import LogItem
from python.helpers import log
import math
from python.extensions.before_main_llm_call._10_log_for_stream import build_heading, build_default_heading


class LogFromStream(Extension):

    async def execute(
        self,
        loop_data: LoopData = LoopData(),
        text: str = "",
        parsed: dict = {},
        **kwargs,
    ):

        heading = build_default_heading(self.agent)
        if "headline" in parsed:
            heading = build_heading(self.agent, parsed['headline'])
        elif "tool_name" in parsed:
            heading = build_heading(self.agent, f"Using {parsed['tool_name']}") # if the llm skipped headline
        elif "thoughts" in parsed:
            # thought length indicator
            length = "|" * math.ceil(math.sqrt(len(text))/2)
            heading = build_heading(self.agent, f"Thinking... {length}")
        else:
            heading = build_heading(self.agent, "Receiving...")
        
        # create log message and store it in loop data temporary params
        if "log_item_generating" not in loop_data.params_temporary:
            loop_data.params_temporary["log_item_generating"] = (
                self.agent.context.log.log(
                    type="agent",
                    heading=heading,
                )
            )

        # update log message
        log_item = loop_data.params_temporary["log_item_generating"]

        # keep reasoning from previous logs in kvps
        kvps = {}
        if log_item.kvps is not None and "reasoning" in log_item.kvps:
            kvps["reasoning"] = log_item.kvps["reasoning"]
        
        # step description for UI - using tool XY, writing Python code, etc.
        if parsed is not None and "tool_name" in parsed and parsed["tool_name"]:
            kvps["step"] = f"Using {parsed['tool_name']}..." # using tool XY
            if parsed["tool_name"]=="code_execution_tool":
                if "tool_args" in parsed and "runtime" in parsed["tool_args"]:
                    length = ""
                    if "code" in parsed["tool_args"]:
                        length = f"({len(parsed['tool_args']['code'])})"
                        kvps["step"] = f"Writing code... {length}"
                    if parsed["tool_args"]["runtime"] == "python":
                        kvps["step"] = f"Writing Python code... {length}"
                    elif parsed["tool_args"]["runtime"] == "nodejs":
                        kvps["step"] = f"Writing Node.js code... {length}"
                    elif parsed["tool_args"]["runtime"] == "terminal":
                        kvps["step"] = f"Writing terminal command... {length}"
        kvps.update(parsed)



        # update the log item
        log_item.update(heading=heading, content=text, kvps=kvps)