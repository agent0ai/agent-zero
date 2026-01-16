"""
Hot-Reload Test Tool

Simple tool to test hot-reload functionality.
Modify the response message and save to see instant changes.
"""

from python.helpers.tool import Tool, Response


class HotReloadTest(Tool):
    """Test tool for hot-reload system"""

    async def execute(self, **kwargs) -> Response:
        """Execute the test tool"""

        # Modify this message and save to test hot-reload
        test_message = "Hot-Reload Test v1.0 - The system is working!"

        # Get optional user message
        user_message = self.args.get("message", "")

        if user_message:
            response = f"{test_message}\n\nYour message: {user_message}"
        else:
            response = test_message

        return Response(
            message=response,
            break_loop=False
        )
