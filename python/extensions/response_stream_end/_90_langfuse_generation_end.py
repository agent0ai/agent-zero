from python.helpers.extension import Extension
from python.helpers.tokens import approximate_tokens
from agent import LoopData


class LangfuseGenerationEnd(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        if not loop_data.params_persistent.get("lf_sampled"):
            return

        generation = loop_data.params_temporary.get("lf_generation")
        if not generation:
            return

        response_text = loop_data.last_response or ""
        output_tokens = approximate_tokens(response_text) if response_text else 0
        input_tokens = loop_data.params_temporary.get("lf_generation_input_tokens", 0)

        try:
            generation.update(
                output=response_text[:2000],
                usage_details={
                    "input": input_tokens,
                    "output": output_tokens,
                    "total": input_tokens + output_tokens,
                },
            )
            generation.end()
        except Exception:
            pass
