from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any, Optional


class DeploymentStrategy(ABC):
    """
    Abstract base class for deployment platform strategies.

    Each deployment platform (GitHub Actions, Kubernetes, SSH, AWS, GCP)
    implements this interface to provide platform-specific deployment logic.

    Enhanced with:
    - Progress reporting support
    - Deployment metadata tracking
    - Deployment mode parameter (rolling, blue-green, immediate)
    - Async generator for streaming results
    """

    def __init__(self):
        """Initialize strategy with progress reporter and metadata tracking."""
        self.last_deployment_metadata: Optional[dict] = None
        self.progress_reporter: Optional[Any] = None  # ProgressReporter type

    def set_progress_reporter(self, reporter):
        """
        Set progress reporter for streaming updates.

        Args:
            reporter: ProgressReporter instance
        """
        self.progress_reporter = reporter

    async def _report_progress(self, message: str, percent: Optional[int] = None):
        """
        Helper to report progress if reporter is set.

        Args:
            message: Progress message
            percent: Optional completion percentage
        """
        if self.progress_reporter:
            async for _ in self.progress_reporter.report(message, percent):
                pass  # Consume generator

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
    async def execute_deployment(
        self, config: dict[str, Any], deployment_mode: str = "rolling"
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Execute the actual deployment.

        Args:
            config: Platform-specific configuration
            deployment_mode: Deployment mode (rolling|blue-green|immediate)

        Yields:
            Progress updates and final deployment result:
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
    async def rollback(self) -> AsyncGenerator[dict[str, Any], None]:
        """
        Rollback to previous version.

        Yields:
            Progress updates and final rollback result:
            {
                'rollback_successful': bool,
                'message': 'Rollback details'
            }
        """
        pass
