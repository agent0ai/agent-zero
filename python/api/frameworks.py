from dataclasses import asdict
from python.helpers.api import ApiHandler, Input, Output, Request
from python.helpers import frameworks


class Frameworks(ApiHandler):
    """API handler for development framework operations."""

    async def process(self, input: Input, request: Request) -> Output:
        action = input.get("action", "list")

        try:
            if action == "list":
                data = self.list_frameworks()
            elif action == "get":
                data = self.get_framework(input.get("id", ""))
            else:
                raise Exception(f"Invalid action: {action}")

            return {
                "ok": True,
                "data": data,
            }
        except Exception as e:
            return {
                "ok": False,
                "error": str(e),
            }

    def list_frameworks(self) -> list[dict]:
        """List all available frameworks."""
        return [asdict(fw) for fw in frameworks.list_frameworks()]

    def get_framework(self, framework_id: str) -> dict | None:
        """Get a specific framework by ID."""
        fw = frameworks.get_framework(framework_id)
        if fw is None:
            return None
        return asdict(fw)
