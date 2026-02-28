from __future__ import annotations

from python.helpers.deployment_primitives import normalize_environment
from python.helpers.tool import Response, Tool


class DeploymentValidateEnv(Tool):
    """Validate and normalize deployment environment input."""

    async def execute(self, environment: str = "", **kwargs) -> Response:
        if not environment and self.args:
            environment = str(self.args.get("environment", ""))

        normalized = normalize_environment(environment)
        if not normalized:
            return Response(
                message=(
                    f"Invalid environment: '{environment}'. "
                    "Valid: production|staging|development (prod|stage|dev)"
                ),
                break_loop=False,
                additional={"valid": False, "environment": environment},
            )

        return Response(
            message=f"Environment validated: {normalized}",
            break_loop=False,
            additional={"valid": True, "environment": normalized},
        )
