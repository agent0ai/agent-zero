from __future__ import annotations

from python.helpers.deployment_primitives import record_deployment_result
from python.helpers.tool import Response, Tool


class DeploymentRecordResult(Tool):
    """Record deployment result metadata as a standalone primitive."""

    async def execute(self, environment: str = "", status: str = "", platform: str = "", **kwargs) -> Response:
        if self.args:
            environment = environment or str(self.args.get("environment", ""))
            status = status or str(self.args.get("status", ""))
            platform = platform or str(self.args.get("platform", ""))

        payload = {
            "environment": environment,
            "status": status or "unknown",
            "platform": platform or "default",
        }
        record = record_deployment_result(payload)
        return Response(
            message=(
                f"Deployment result recorded for {payload['environment'] or 'unknown'} "
                f"with status {payload['status']}"
            ),
            break_loop=False,
            additional=record,
        )
