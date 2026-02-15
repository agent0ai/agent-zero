import json
from python.helpers.api import ApiHandler, Input, Output, Request, Response
from python.helpers import files, settings
import models
from models import ModelConfig, ModelType


class PromptRefine(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        system_prompt = input.get("system_prompt", "")
        user_message = input.get("user_message", "")
        response_text = input.get("response", "")
        model_name = input.get("model", "")
        token_count = input.get("token_count", 0)

        if not system_prompt:
            return {"success": False, "error": "system_prompt is required"}

        # Load refiner system prompt
        try:
            refiner_prompt = files.read_file("prompts/prompt_refiner.md")
        except Exception:
            return {"success": False, "error": "Refiner prompt template not found"}

        # Build the user message for the refiner
        refiner_input = (
            f"## Original System Prompt\n\n{system_prompt}\n\n"
            f"## User Message\n\n{user_message}\n\n"
            f"## LLM Response\n\n{response_text}\n\n"
            f"## Metadata\n\n- Model: {model_name}\n- Tokens: {token_count}\n"
        )

        # Use the utility model (cheaper/faster) for refinement
        try:
            set = settings.get_settings()
            provider = set.get("util_model_provider", "")
            name = set.get("util_model_name", "")

            if not provider or not name:
                return {"success": False, "error": "Utility model not configured"}

            model_conf = ModelConfig(
                type=ModelType.CHAT,
                provider=provider,
                name=name,
                api_base=set.get("util_model_api_base", ""),
                ctx_length=set.get("util_model_ctx_length", 0),
                limit_requests=set.get("util_model_rl_requests", 0),
                limit_input=set.get("util_model_rl_input", 0),
                limit_output=set.get("util_model_rl_output", 0),
                kwargs=set.get("util_model_kwargs", {}),
            )

            llm = models.get_chat_model(
                provider=provider,
                name=name,
                model_config=model_conf,
                **model_conf.build_kwargs(),
            )

            response, _reasoning = await llm.unified_call(
                system_message=refiner_prompt,
                user_message=refiner_input,
            )

            # Parse the JSON response — strip markdown code fences if present
            content = response.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[-1]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

            variants = json.loads(content)

            return {
                "success": True,
                "variants": variants,
            }
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Failed to parse refiner output: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Refiner failed: {e}"}
