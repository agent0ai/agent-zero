"""Shared factory logic for all three @extensible secrets hooks.

Centralises OpenBao manager creation and availability checks
so the three extension entry points stay thin.
"""
from __future__ import annotations

import logging
import threading
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from helpers.secrets import SecretsManager

logger = logging.getLogger(__name__)

# Module-level singleton — shared across all three factory extensions
_manager: Optional["SecretsManager"] = None
_init_lock = threading.Lock()
_init_attempted = False


def get_openbao_manager() -> Optional["SecretsManager"]:
    """Get or create the shared OpenBaoSecretsManager singleton.

    Returns the manager if OpenBao is configured and available,
    None otherwise (letting the default .env path proceed).

    Thread-safe: uses a lock to ensure single initialization.
    """
    global _manager, _init_attempted

    if _manager is not None:
        # Fast path — already initialized
        return _manager if _manager.is_available() else None

    if _init_attempted:
        # Already tried and failed — don't retry on every call
        return None

    with _init_lock:
        # Double-check after acquiring lock
        if _manager is not None:
            return _manager if _manager.is_available() else None
        if _init_attempted:
            return None

        _init_attempted = True

        try:
            from helpers.plugins import find_plugin_dir
            from helpers.secrets import DEFAULT_SECRETS_FILE

            # Find our plugin directory for settings.json
            plugin_dir = find_plugin_dir("openbao-secrets")
            if not plugin_dir:
                logger.debug("openbao-secrets plugin directory not found")
                return None

            # Load and validate config
            # Import from plugin's own helpers
            import importlib.util
            import os

            config_path = os.path.join(plugin_dir, "helpers", "config.py")
            spec = importlib.util.spec_from_file_location("openbao_config", config_path)
            config_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_mod)

            config = config_mod.load_config(plugin_dir)
            errors = config_mod.validate_config(config)

            if not config.enabled:
                logger.debug("OpenBao plugin is disabled")
                return None

            if errors:
                logger.warning("OpenBao config validation errors: %s", errors)
                return None

            # Load the manager module
            manager_path = os.path.join(plugin_dir, "helpers", "openbao_secrets_manager.py")
            spec_mgr = importlib.util.spec_from_file_location("openbao_manager", manager_path)
            mgr_mod = importlib.util.module_from_spec(spec_mgr)

            # Ensure the client module is loadable too
            client_path = os.path.join(plugin_dir, "helpers", "openbao_client.py")
            spec_client = importlib.util.spec_from_file_location("openbao_client", client_path)
            client_mod = importlib.util.module_from_spec(spec_client)
            spec_client.loader.exec_module(client_mod)

            # Inject dependencies for the manager module
            import sys
            sys.modules["helpers.openbao_client"] = client_mod
            sys.modules["helpers.config"] = config_mod

            spec_mgr.loader.exec_module(mgr_mod)

            _manager = mgr_mod.OpenBaoSecretsManager.get_or_create(
                config, DEFAULT_SECRETS_FILE
            )

            if _manager.is_available():
                logger.info("OpenBao secrets manager initialized successfully")
                return _manager
            else:
                logger.warning("OpenBao manager created but not available")
                if config.fallback_to_env:
                    # Return the manager anyway — it will handle fallback internally
                    return _manager
                return None

        except ImportError as exc:
            logger.warning("OpenBao plugin dependencies not installed: %s", exc)
            return None
        except Exception as exc:
            logger.error("Failed to initialize OpenBao secrets manager: %s", exc)
            return None


def reset():
    """Reset the singleton — for testing."""
    global _manager, _init_attempted
    with _init_lock:
        _manager = None
        _init_attempted = False
