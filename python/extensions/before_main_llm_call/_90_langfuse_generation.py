from python.helpers.extension import Extension
from python.helpers.tokens import approximate_tokens
from agent import LoopData


class LangfuseGenerationStart(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        if not loop_data.params_persistent.get("lf_sampled"):
            return

        parent = loop_data.params_temporary.get("lf_iteration_span")
        if not parent:
            parent = loop_data.params_persistent.get("lf_trace")
        if not parent:
            return

        model = self.agent.get_chat_model()
        model_name = getattr(model, "model_name", "unknown") if model else "unknown"

        prompt_summary = ""
        if loop_data.system:
            system_text = " ".join(str(s) for s in loop_data.system[:3])
            prompt_summary = system_text[:1000]

        generation = parent.start_generation(
            name="main-llm",
            model=model_name,
            input=prompt_summary,
            metadata={
                "agent_number": self.agent.number,
                "iteration": loop_data.iteration,
            },
        )
        loop_data.params_temporary["lf_generation"] = generation
        loop_data.params_temporary["lf_generation_input_tokens"] = approximate_tokens(prompt_summary)
