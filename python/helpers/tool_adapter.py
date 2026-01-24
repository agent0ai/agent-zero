"""
Tool Adapter - Adapts tool calling to model capabilities
Converts between function calling formats and ReAct patterns
"""

import json
import re
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolCallStrategy:
    """Strategy for tool calling based on model capabilities"""

    format: str  # "native", "hermes", "react"
    parser: str | None
    requires_preprocessing: bool
    requires_postprocessing: bool


class ToolAdapter:
    """
    Adapts tool calling format to model capabilities

    - Native (OpenAI-style): For models with function_calling capability
    - Hermes: For Qwen models with Hermes-style support
    - ReAct: Universal fallback pattern
    """

    @staticmethod
    def get_strategy(model_info) -> ToolCallStrategy:
        """Determine best tool calling strategy for model"""

        if model_info.supports_native_tools:
            return ToolCallStrategy(
                format="native", parser=None, requires_preprocessing=False, requires_postprocessing=False
            )

        if model_info.supports_hermes_tools:
            return ToolCallStrategy(
                format="hermes",
                parser=model_info.tool_parser or "hermes",
                requires_preprocessing=True,
                requires_postprocessing=True,
            )

        # Fallback to ReAct
        return ToolCallStrategy(format="react", parser=None, requires_preprocessing=True, requires_postprocessing=True)

    @staticmethod
    def preprocess_tools_for_model(tools: list[dict], strategy: ToolCallStrategy) -> Any:
        """Convert tool definitions to model-specific format"""

        if strategy.format == "native":
            return tools  # Already in OpenAI format

        if strategy.format == "hermes":
            return {"tools": tools, "tool_choice": "auto"}

        if strategy.format == "react":
            # Convert to ReAct prompt format
            tool_descriptions = []
            for tool in tools:
                desc = f"- {tool['name']}: {tool.get('description', 'No description')}"
                tool_descriptions.append(desc)

            return "\n".join(
                [
                    "You have access to the following tools:",
                    *tool_descriptions,
                    "",
                    "Use the format:",
                    "Thought: [your reasoning]",
                    "Action: [tool_name]",
                    "Action Input: [tool_parameters as JSON]",
                ]
            )

    @staticmethod
    def postprocess_model_response(response: str, strategy: ToolCallStrategy) -> dict:
        """Extract tool calls from model response"""

        if strategy.format == "native":
            return response  # Already structured

        if strategy.format == "hermes":
            return response  # Hermes format parsed elsewhere

        if strategy.format == "react":
            # Parse ReAct format
            action_match = re.search(r"Action:\s*(.+?)$", response, re.MULTILINE)
            input_match = re.search(r"Action Input:\s*(.+?)$", response, re.MULTILINE | re.DOTALL)

            if action_match and input_match:
                try:
                    return {
                        "tool": action_match.group(1).strip(),
                        "parameters": json.loads(input_match.group(1).strip()),
                    }
                except:
                    pass

            return None
