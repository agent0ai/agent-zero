import asyncio
from datetime import datetime, timezone

from agent import LoopData
from python.helpers import settings
from python.helpers.extension import Extension


class PromptEnhancer(Extension):
    """
    Prompt enhancement extension with context-aware suggestions.

    Features:
    - Enhances user prompts with structure and clarity
    - Analyzes context to suggest relevant tools/workflows
    - Integrates with LLM Router for model selection (when enabled)
    """

    # Keywords that suggest specific tools/features
    TOOL_SUGGESTIONS = {
        # Customer/Business keywords -> customer_lifecycle
        "customer": "customer_lifecycle",
        "client": "customer_lifecycle",
        "lead": "customer_lifecycle",
        "prospect": "customer_lifecycle",
        "sales": "customer_lifecycle",
        "crm": "customer_lifecycle",
        # Project/Portfolio keywords -> portfolio_manager_tool
        "project": "portfolio_manager_tool",
        "portfolio": "portfolio_manager_tool",
        "milestone": "portfolio_manager_tool",
        "deliverable": "portfolio_manager_tool",
        # Workflow keywords -> workflow_engine
        "workflow": "workflow_engine",
        "stage": "workflow_engine",
        "process": "workflow_engine",
        "pipeline": "workflow_engine",
        # Diagram keywords -> diagram_tool
        "diagram": "diagram_tool",
        "architecture": "diagram_tool",
        "flowchart": "diagram_tool",
        "visualization": "diagram_tool",
        # Email keywords -> email
        "email": "email",
        "send email": "email",
        "mail": "email",
        # Deployment keywords -> deployment_orchestrator
        "deploy": "deployment_orchestrator",
        "deployment": "deployment_orchestrator",
        "ci/cd": "deployment_orchestrator",
        "docker": "deployment_orchestrator",
        "kubernetes": "deployment_orchestrator",
        # Analysis keywords -> business_xray_tool
        "analyze": "business_xray_tool",
        "roi": "business_xray_tool",
        "business case": "business_xray_tool",
        "cost benefit": "business_xray_tool",
    }

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        set = settings.get_settings()
        if not set.get("prompt_enhance_enabled", False):
            return

        if not loop_data.user_message:
            return

        if loop_data.params_temporary.get("prompt_enhanced"):
            return

        user_text = loop_data.user_message.output_text()
        if not user_text.strip():
            return

        max_chars = int(set.get("prompt_enhance_max_chars", 0) or 0)
        if max_chars > 0 and len(user_text) > max_chars:
            user_text = user_text[:max_chars]

        # Analyze context for tool suggestions
        suggested_tools = self._analyze_context(user_text)

        # Build enhanced system prompt with context
        system_prompt = self.agent.read_prompt("prompt.enhance.sys.md")

        # Add tool suggestions to the enhancement prompt if any detected
        tool_context = ""
        if suggested_tools:
            tool_list = ", ".join(suggested_tools)
            tool_context = f"\n\nRelevant Agent Jumbo tools for this request: {tool_list}"

        message_prompt = self.agent.read_prompt("prompt.enhance.msg.md", user_message=user_text) + tool_context

        try:
            # Keep enhancement from blocking the main execution path.
            timeout_seconds = int(set.get("prompt_enhance_timeout_seconds", 8) or 8)
            enhanced = await asyncio.wait_for(
                self._call_enhance_model(system_prompt, message_prompt),
                timeout=timeout_seconds,
            )
        except TimeoutError:
            self.agent.context.log.log(
                type="warning",
                content=("Prompt enhancement timed out. " "Continuing with original user prompt."),
            )
            if set.get("prompt_enhance_fail_open", True):
                return
            raise
        except Exception as e:
            self.agent.context.log.log(type="warning", content=f"Prompt enhancement failed: {e}")
            return

        enhanced = enhanced.strip()
        if not enhanced:
            return

        payload = {
            "original": user_text,
            "enhanced": enhanced,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "suggested_tools": suggested_tools,
        }
        self.agent.context.set_output_data("prompt_enhance_last", payload)
        self.agent.context.log.log(
            type="info",
            heading="Prompt enhancement applied",
            content="Enhanced prompt generated for the current request.",
            kvps=payload,
        )

        loop_data.extras_temporary["enhanced_prompt"] = self.agent.read_prompt(
            "agent.system.prompt_enhanced.md",
            enhanced_prompt=enhanced,
            original_prompt=user_text,
        )
        loop_data.params_temporary["prompt_enhanced"] = True

    def _analyze_context(self, user_text: str) -> list:
        """Analyze user text and suggest relevant tools."""
        suggested = set()
        text_lower = user_text.lower()

        for keyword, tool in self.TOOL_SUGGESTIONS.items():
            if keyword in text_lower:
                suggested.add(tool)

        return list(suggested)

    async def _call_enhance_model(self, system: str, message: str) -> str:
        """
        Call the enhancement model, using LLM Router if enabled.
        Falls back to the default utility model if router not available.
        """
        set = settings.get_settings()
        use_router = set.get("llm_router_enabled", False)

        if use_router:
            try:
                from python.helpers.llm_router import RoutingPriority, get_router

                router = get_router()
                # Select a fast, cheap model for enhancement
                model_info = router.select_model(
                    role="utility",
                    context_type="enhancement",
                    priority=RoutingPriority.SPEED,  # Prefer speed for preprocessing
                    required_capabilities=["chat"],
                )

                if model_info:
                    # Use the router-selected model
                    import models
                    from models import ModelConfig, ModelType

                    model_config = ModelConfig(
                        type=ModelType.CHAT,
                        provider=model_info.provider,
                        name=model_info.name,
                        ctx_length=model_info.context_length,
                    )
                    model = models.get_chat_model(
                        model_info.provider,
                        model_info.name,
                        model_config=model_config,
                    )
                    result, _ = await model.unified_call(system_message=system, user_message=message)

                    # Record usage for tracking
                    router.record_call(
                        provider=model_info.provider,
                        model_name=model_info.name,
                        role="utility",
                        input_tokens=len(message) // 4,
                        output_tokens=len(result) // 4,
                        success=True,
                    )

                    return result
            except Exception as e:
                self.agent.context.log.log(type="debug", content=f"LLM Router selection failed, using default: {e}")

        # Fallback to default utility model
        return await self.agent.call_utility_model(system=system, message=message)
