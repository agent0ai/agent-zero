from python.helpers.extension import Extension
from agent import LoopData


class IncludeGithubStatus(Extension):
    """Inject GitHub connection status into agent context."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        # Import here to avoid circular imports
        from python.api.github_callback import get_github_auth

        auth_data = get_github_auth()
        if not auth_data:
            return  # Not connected, don't add to context

        access_token = auth_data.get("access_token")
        user = auth_data.get("user")

        if not access_token or not user:
            return  # Incomplete auth data

        # Build the GitHub status prompt
        github_prompt = self.agent.read_prompt(
            "agent.extras.github_status.md",
            username=user.get("login", "unknown"),
            name=user.get("name") or user.get("login", ""),
            avatar_url=user.get("avatar_url", ""),
        )

        # Add to agent's context
        loop_data.extras_temporary["github_status"] = github_prompt
