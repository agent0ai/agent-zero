from collections.abc import AsyncGenerator
from typing import Any

from python.tools.deployment_strategies.base import DeploymentStrategy


class SSHStrategy(DeploymentStrategy):
    """
    SSH deployment strategy for traditional server deployments.

    Supports:
    - Remote script execution via SSH
    - Service restart via systemd/init.d
    - Health checks via service status
    - Rollback via backup restoration
    """

    def __init__(self):
        super().__init__()
        self.last_host = None

    async def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate SSH-specific configuration"""
        if "host" not in config:
            raise ValueError("host is required for SSH deployments")

        if "deploy_script" not in config:
            raise ValueError("deploy_script is required for SSH deployments")

        return True

    async def execute_deployment(
        self, config: dict[str, Any], deployment_mode: str = "rolling"
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Execute SSH deployment.

        POC Implementation: Returns simulated success.
        Full implementation will use paramiko/fabric to SSH and run commands.
        """
        host = config["host"]
        self.last_host = host

        yield {"status": "success", "host": host, "message": f"Deployed to {host} via SSH"}

    async def run_smoke_tests(self, config: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        """
        Run smoke tests after SSH deployment.

        POC Implementation: Returns simulated results.
        Full implementation will SSH to server and check service status.
        """
        results = {"service_running": True, "http_responding": True}

        return True, results

    async def rollback(self) -> AsyncGenerator[dict[str, Any], None]:
        """
        Rollback SSH deployment.

        POC Implementation: Returns simulated success.
        Full implementation will SSH and restore from backup.
        """
        yield {
            "rollback_successful": True,
            "host": self.last_host,
            "message": f"Rolled back deployment on {self.last_host}",
        }
