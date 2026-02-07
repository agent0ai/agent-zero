from typing import Any
from python.helpers.files import VariablesPlugin


class GithubToolVariables(VariablesPlugin):
    """Provide variables for the GitHub tool prompt."""

    def get_variables(
        self, file: str, backup_dirs: list[str] | None = None, **kwargs
    ) -> dict[str, Any]:
        # Import here to avoid circular imports
        from python.api.github_callback import get_github_auth

        auth_data = get_github_auth()

        if not auth_data:
            return {"github_connected": False, "github_username": ""}

        access_token = auth_data.get("access_token")
        user = auth_data.get("user")

        if not access_token or not user:
            return {"github_connected": False, "github_username": ""}

        return {
            "github_connected": True,
            "github_username": user.get("login", "unknown"),
        }
