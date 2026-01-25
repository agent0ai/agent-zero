from abc import ABC, abstractmethod
from typing import Any


class DeploymentStrategy(ABC):
    """
    Abstract base class for deployment platform strategies.

    Each deployment platform (GitHub Actions, Kubernetes, SSH, AWS, GCP)
    implements this interface to provide platform-specific deployment logic.
    """

    @abstractmethod
    async def validate_config(self, config: dict[str, Any]) -> bool:
        """
        Validate platform-specific configuration.

        Args:
            config: Platform-specific configuration dictionary

        Returns:
            True if config is valid, False otherwise

        Raises:
            ValueError: If config is invalid with specific error message
        """
        pass

    @abstractmethod
    async def execute_deployment(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the actual deployment.

        Args:
            config: Platform-specific configuration

        Returns:
            Dictionary with deployment result:
            {
                'status': 'success'|'failed',
                'message': 'Deployment details',
                ... platform-specific fields
            }
        """
        pass

    @abstractmethod
    async def run_smoke_tests(self, config: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        """
        Run immediate smoke tests after deployment.

        Args:
            config: Platform-specific configuration with health check settings

        Returns:
            Tuple of (all_passed: bool, results: dict)
        """
        pass

    @abstractmethod
    async def rollback(self) -> dict[str, Any]:
        """
        Rollback to previous version.

        Returns:
            Dictionary with rollback result:
            {
                'rollback_successful': bool,
                'message': 'Rollback details'
            }
        """
        pass
