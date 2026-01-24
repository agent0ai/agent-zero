"""
Tests for adaptive tool calling system
"""

from unittest.mock import Mock

import pytest

from python.helpers.tool_adapter import ToolAdapter, ToolCallStrategy


class TestToolAdapter:
    """Test tool calling adaptation"""

    def test_native_tools_strategy(self):
        """Models with native tool support should use native format"""
        model_info = Mock()
        model_info.supports_native_tools = True
        model_info.supports_hermes_tools = False
        model_info.supports_react_tools = False

        strategy = ToolAdapter.get_strategy(model_info)

        assert strategy.format == "native"
        assert not strategy.requires_preprocessing

    def test_hermes_tools_strategy(self):
        """Models with Hermes support should use Hermes format"""
        model_info = Mock()
        model_info.supports_native_tools = False
        model_info.supports_hermes_tools = True
        model_info.supports_react_tools = True
        model_info.tool_parser = "hermes"

        strategy = ToolAdapter.get_strategy(model_info)

        assert strategy.format == "hermes"
        assert strategy.parser == "hermes"

    def test_react_fallback_strategy(self):
        """Models without tool support should fall back to ReAct"""
        model_info = Mock()
        model_info.supports_native_tools = False
        model_info.supports_hermes_tools = False
        model_info.supports_react_tools = True

        strategy = ToolAdapter.get_strategy(model_info)

        assert strategy.format == "react"

    def test_preprocess_native_tools(self):
        """Native tools should pass through unchanged"""
        tools = [{"name": "search", "description": "Search the web"}]
        strategy = ToolCallStrategy(
            format="native", parser=None, requires_preprocessing=False, requires_postprocessing=False
        )

        result = ToolAdapter.preprocess_tools_for_model(tools, strategy)

        assert result == tools

    def test_preprocess_react_tools(self):
        """ReAct format should convert to prompt"""
        tools = [
            {"name": "search", "description": "Search the web"},
            {"name": "calculator", "description": "Calculate math"},
        ]
        strategy = ToolCallStrategy(
            format="react", parser=None, requires_preprocessing=True, requires_postprocessing=True
        )

        result = ToolAdapter.preprocess_tools_for_model(tools, strategy)

        assert isinstance(result, str)
        assert "search" in result
        assert "calculator" in result
        assert "Action:" in result

    def test_postprocess_react_response(self):
        """Should extract tool call from ReAct format"""
        response = """
Thought: I need to search for information
Action: search
Action Input: {"query": "Python tutorials"}
"""
        strategy = ToolCallStrategy(
            format="react", parser=None, requires_preprocessing=True, requires_postprocessing=True
        )

        result = ToolAdapter.postprocess_model_response(response, strategy)

        assert result is not None
        assert result["tool"] == "search"
        assert result["parameters"]["query"] == "Python tutorials"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
