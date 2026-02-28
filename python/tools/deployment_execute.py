from __future__ import annotations

from python.helpers.deployment_primitives import execute_deployment, normalize_environment
from python.helpers.tool import Response, Tool


class DeploymentExecute(Tool):
    """Execute deployment as a standalone primitive."""

    async def execute(self, environment: str = "", platform: str = "", **kwargs) -> Response:
        if self.args:
            environment = environment or str(self.args.get("environment", ""))
            platform = platform or str(self.args.get("platform", ""))

        normalized = normalize_environment(environment)
        if not normalized:
            return Response(
                message=f"Cannot deploy: invalid environment '{environment}'",
                break_loop=False,
                additional={"status": "failed"},
            )

        result = execute_deployment(normalized, platform=platform or None)
        return Response(
            message=f"Deployment executed for {normalized} on {result['platform']}",
            break_loop=False,
            additional=result,
        )
