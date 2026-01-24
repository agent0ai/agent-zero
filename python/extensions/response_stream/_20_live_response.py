from python.helpers.extension import Extension
from agent import LoopData


class LiveResponse(Extension):

    async def execute(
        self,
        loop_data: LoopData = LoopData(),
        _text: str = "",
        parsed: dict | None = None,
        **kwargs,
    ):
        try:
            parsed = parsed if isinstance(parsed, dict) else {}
            tool_args = parsed.get("tool_args")
            is_response = parsed.get("tool_name") == "response"
            has_text = isinstance(tool_args, dict) and bool(tool_args.get("text"))
            if not (is_response and has_text):
                return  # not a response

            # create log message and store it in loop data temporary params
            if "log_item_response" not in loop_data.params_temporary:
                loop_data.params_temporary["log_item_response"] = (
                    self.agent.context.log.log(
                        type="response",
                        heading=f"icon://chat {self.agent.agent_name}: Responding",
                    )
                )

            # update log message
            log_item = loop_data.params_temporary["log_item_response"]
            log_item.update(content=parsed["tool_args"]["text"])
        except Exception:
            pass
