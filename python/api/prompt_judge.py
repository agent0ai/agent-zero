import json

import models
from python.helpers.api import ApiHandler, Input, Output, Request, Response
from python.helpers import files, settings


class PromptJudge(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        original_prompt = input.get("original_prompt", "")
        original_response = input.get("original_response", "")
        variants = input.get("variants", [])

        if not original_prompt:
            return {"success": False, "error": "original_prompt is required"}
        if not variants:
            return {"success": False, "error": "variants is required"}

        # Load judge system prompt
        try:
            judge_prompt = files.read_file("prompts/prompt_judge.md")
        except FileNotFoundError:
            return {"success": False, "error": "Judge prompt template not found"}

        # Build the input for the judge
        variants_text = ""
        for i, v in enumerate(variants):
            prompt_text = v.get("prompt", "") if isinstance(v, dict) else str(v)
            explanation = v.get("explanation", "") if isinstance(v, dict) else ""
            variants_text += (
                f"### Variant {i}\n\n"
                f"**Prompt:**\n{prompt_text}\n\n"
                f"**Explanation:** {explanation}\n\n"
            )

        judge_input = (
            f"## Original System Prompt\n\n{original_prompt}\n\n"
            f"## Original Response\n\n{original_response}\n\n"
            f"## Variants to Judge\n\n{variants_text}"
        )

        try:
            from langchain_core.messages import SystemMessage, HumanMessage

            set = settings.get_settings()

            # Use the utility model for judging (cheaper, deterministic)
            provider = set.get("util_model_provider", "")
            model_name = set.get("util_model_name", "")
            api_base = set.get("util_model_api_base", "")

            kwargs = {}
            if api_base:
                kwargs["api_base"] = api_base
            kwargs.update(set.get("util_model_kwargs", {}))

            llm = models.get_chat_model(
                provider=provider,
                name=model_name,
                **kwargs,
            )

            messages = [
                SystemMessage(content=judge_prompt),
                HumanMessage(content=judge_input),
            ]

            result = await llm.ainvoke(messages)
            content = result.content if hasattr(result, "content") else str(result)

            # Parse JSON — strip markdown code fences if present
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[-1]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

            results = json.loads(content)

            return {
                "success": True,
                "results": results,
            }
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Failed to parse judge output: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Judge failed: {e}"}
