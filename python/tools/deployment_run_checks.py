from __future__ import annotations

from python.helpers.deployment_primitives import normalize_environment, run_predeployment_checks
from python.helpers.tool import Response, Tool


class DeploymentRunChecks(Tool):
    """Run pre-deployment checks as a standalone primitive."""

    async def execute(self, environment: str = "", skip_tests: bool = False, skip_backup: bool = False, **kwargs) -> Response:
        if self.args:
            environment = environment or str(self.args.get("environment", ""))
            skip_tests = self._to_bool(self.args.get("skip_tests", skip_tests))
            skip_backup = self._to_bool(self.args.get("skip_backup", skip_backup))

        normalized = normalize_environment(environment)
        if not normalized:
            return Response(
                message=f"Cannot run checks: invalid environment '{environment}'",
                break_loop=False,
                additional={"status": "failed"},
            )

        checks = run_predeployment_checks(normalized, skip_tests=skip_tests, skip_backup=skip_backup)
        return Response(
            message=f"Pre-deployment checks passed for {normalized}",
            break_loop=False,
            additional=checks,
        )

    @staticmethod
    def _to_bool(value) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "y", "on"}
        return bool(value)
