"""
Tests for OpenCode bridge tool
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from python.tools.opencode_bridge import OpenCodeBridge


class TestOpenCodeBridge:
    """Test OpenCode bridge functionality"""

    def create_tool(self, args):
        """Helper to create tool instance with required parameters"""
        mock_agent = Mock()
        mock_agent.agent_name = "test_agent"
        return OpenCodeBridge(agent=mock_agent, name="opencode", method=None, args=args, message="", loop_data=None)

    @pytest.mark.asyncio
    async def test_requires_task_parameter(self):
        """Should return error when task parameter missing"""
        tool = self.create_tool(args={})

        response = await tool.execute()

        assert "Error" in response.message
        assert "task" in response.message.lower()

    @pytest.mark.asyncio
    async def test_executes_opencode_command(self):
        """Should execute OpenCode CLI with correct parameters"""
        tool = self.create_tool(
            args={"task": "Generate a Python function to calculate factorial", "model": "qwen2.5-coder:7b"}
        )

        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"def factorial(n): return 1 if n <= 1 else n * factorial(n-1)", b"")
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
            response = await tool.execute()

            # Verify command called correctly
            mock_exec.assert_called_once()
            call_args = mock_exec.call_args[0]
            assert "npx" in call_args
            assert "--model" in call_args
            assert "qwen2.5-coder:7b" in call_args

            # Verify response
            assert "factorial" in response.message.lower()

    @pytest.mark.asyncio
    async def test_handles_opencode_error(self):
        """Should handle OpenCode execution errors gracefully"""
        tool = self.create_tool(args={"task": "Invalid task"})

        # Mock failed subprocess
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"Error: Model not found")
        mock_process.returncode = 1

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            response = await tool.execute()

            assert "Error" in response.message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
