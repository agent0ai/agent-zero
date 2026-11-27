from helpers import persist_chat, tokens
from helpers.extension import Extension
from helpers import extension
from helpers.print_style import PrintStyle
from agent import LoopData
import asyncio
from helpers.log import LogItem
from helpers import log
import math
import json
from extensions.python.before_main_llm_call._10_log_for_stream import build_heading, build_default_heading


def _args_suffix(args: object) -> str:
    if isinstance(args, dict) and args:
        try:
            length = len(json.dumps(args, separators=(",", ":"), ensure_ascii=False, default=str))
        except (TypeError, ValueError):
            length = len(repr(args))
        return f" ({length})"
    return ""


async def build_step_description(agent, parsed: dict) -> str:
    """Build the one-line UI step text for a streamed tool call."""
    tool_name = str(parsed.get("tool_name") or "")
    step = f"Using {tool_name.replace('_', ' ')}..."
    suffix = _args_suffix(parsed.get("tool_args"))
    ctx = {
        "tool_name": tool_name,
        "tool_args": parsed.get("tool_args"),
        "step": step,
    }
    # step text is display-only: a broken hook must not abort the stream chunk
    try:
        await extension.call_extensions_async("tool_step_description", agent, ctx=ctx)
    except Exception as e:
        PrintStyle.debug("tool_step_description hook failed:", e)
        return f"{step}{suffix}"
    return f"{ctx['step']}{suffix}"


class LogFromStream(Extension):

    async def execute(
        self,
        loop_data: LoopData = LoopData(),
        text: str = "",
        parsed: dict = {},
        **kwargs,
    ):
        if not self.agent:
            return

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
        
        # step description for UI; plugins refine it through the hook
        if parsed is not None and "tool_name" in parsed and parsed["tool_name"]:
            kvps["step"] = await build_step_description(self.agent, parsed)
        kvps.update(parsed)



        # update the log item
        log_item.update(heading=heading, content=text, kvps=kvps)
