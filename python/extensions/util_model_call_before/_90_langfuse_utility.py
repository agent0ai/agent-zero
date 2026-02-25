from python.helpers.extension import Extension
from python.helpers.tokens import approximate_tokens


class LangfuseUtilityGeneration(Extension):

    async def execute(self, call_data: dict = {}, **kwargs):
        loop_data = self.agent.loop_data
        if not loop_data or not loop_data.params_persistent.get("lf_sampled"):
            return

        parent = loop_data.params_temporary.get("lf_iteration_span")
        if not parent:
            parent = loop_data.params_persistent.get("lf_trace")
        if not parent:
            return

        model = call_data.get("model")
        model_name = getattr(model, "model_name", "unknown") if model else "unknown"

        system_msg = str(call_data.get("system", ""))[:500]
        user_msg = str(call_data.get("message", ""))[:500]
        input_text = f"System: {system_msg}\nUser: {user_msg}" if system_msg else user_msg

        generation = parent.start_generation(
            name="utility-llm",
            model=model_name,
            input=input_text,
            metadata={
                "agent_number": self.agent.number,
                "call_type": "utility",
            },
        )
        loop_data.params_temporary["lf_utility_gen"] = generation
