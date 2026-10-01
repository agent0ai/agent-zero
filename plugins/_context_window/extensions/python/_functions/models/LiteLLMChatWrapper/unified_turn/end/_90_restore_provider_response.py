from helpers.extension import Extension
from helpers.llm_result import LLMResult


RESPONSE_KEY = "_context_window_accepted_response"


class RestoreProviderResponse(Extension):
    def execute(self, data: dict, **kwargs):
        response = data.pop(RESPONSE_KEY, None)
        result = data.get("result")
        if (
            response is None
            or data.get("exception")
            or not isinstance(result, LLMResult)
            or result.mode != "chat_completions"
        ):
            return

        result.response = response
        if not result.output_items:
            result.output_items = LLMResult.from_chat(
                response=response, reasoning=result.reasoning
            ).output_items
