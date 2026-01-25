from typing import Any

import yaml


class DeploymentConfig:
    """
    Handles loading, merging, and validating deployment configurations.

    Supports:
    - Loading from YAML files
    - Merging configs (explicit params > file config)
    - Platform validation
    """

    VALID_PLATFORMS = ["github-actions", "kubernetes", "ssh", "aws", "gcp"]

    def load_from_file(self, filepath: str) -> dict[str, Any]:
        """
        Load configuration from YAML file.

        Args:
            filepath: Path to YAML config file

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        try:
            with open(filepath) as f:
                config = yaml.safe_load(f)
                return config if config else {}
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found: {filepath}")

    def merge_configs(self, file_config: dict[str, Any], explicit_params: dict[str, Any]) -> dict[str, Any]:
        """
        Merge configs with explicit params taking precedence.

        Args:
            file_config: Configuration from file
            explicit_params: Explicit parameters from tool invocation

        Returns:
            Merged configuration dictionary
        """
        merged = file_config.copy()
        merged.update(explicit_params)
        return merged

    def validate_platform(self, platform: str) -> bool:
        """
        Validate that platform is supported.

        Args:
            platform: Platform name to validate

        Returns:
            True if valid

        Raises:
            ValueError: If platform is not supported
        """
        if platform not in self.VALID_PLATFORMS:
            raise ValueError(f"Invalid platform: '{platform}'. " f"Valid platforms: {', '.join(self.VALID_PLATFORMS)}")
        return True
