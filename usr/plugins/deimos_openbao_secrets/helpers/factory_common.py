"""Shared factory logic for all three @extensible secrets hooks.

Centralises OpenBao manager creation so the three extension
entry points stay thin.

Fallback behaviour:
    When OpenBao is enabled and configured, the factory ALWAYS returns
    the OpenBaoSecretsManager — even if OpenBao is currently unreachable.
    The manager itself decides whether to fall back to .env files based
    on the `fallback_to_env` config setting.

    This prevents the framework from silently using the default .env
    manager when the user has explicitly configured OpenBao.
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

    Returns the manager if OpenBao is enabled and configured,
    None otherwise (letting the default .env path proceed).

    When the manager IS returned, it handles fallback internally:
        - fallback_to_env=True  -> OpenBao first, then .env on failure
        - fallback_to_env=False -> OpenBao only, empty dict on failure

    Thread-safe: uses a lock to ensure single initialization.
    """
    global _manager, _init_attempted

    if _manager is not None:
        # Fast path — already initialized and returned regardless of
        # current OpenBao availability. The manager handles fallback.
        return _manager

    if _init_attempted:
        # Already tried and failed — don't retry on every call
        return None

    with _init_lock:
        # Double-check after acquiring lock
        if _manager is not None:
            return _manager
        if _init_attempted:
            return None

        _init_attempted = True

        try:
            # Auto-install dependencies (hvac, tenacity, circuitbreaker)
            from helpers.deps import ensure_dependencies as _ensure_deps
        except ImportError:
            # If helpers.deps can't be imported, try via plugin dir
            import importlib.util as _ilu
            _dp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "deps.py")
            _sp = _ilu.spec_from_file_location("openbao_deps", _dp)
            _dm = _ilu.module_from_spec(_sp)
            _sp.loader.exec_module(_dm)
            _ensure_deps = _dm.ensure_dependencies

        if not _ensure_deps():
            logger.warning("OpenBao plugin dependencies not available")
            return None

        try:
            from helpers.plugins import find_plugin_dir
            from helpers.secrets import DEFAULT_SECRETS_FILE

            # Find our plugin directory for settings.json
            plugin_dir = find_plugin_dir("deimos_openbao_secrets")
            if not plugin_dir:
                logger.debug("deimos_openbao_secrets plugin directory not found")
                return None

            # Load and validate config
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

            # Load the client and manager modules
            client_path = os.path.join(plugin_dir, "helpers", "openbao_client.py")
            spec_client = importlib.util.spec_from_file_location("openbao_client", client_path)
            client_mod = importlib.util.module_from_spec(spec_client)
            spec_client.loader.exec_module(client_mod)

            manager_path = os.path.join(plugin_dir, "helpers", "openbao_secrets_manager.py")
            spec_mgr = importlib.util.spec_from_file_location("openbao_manager", manager_path)
            mgr_mod = importlib.util.module_from_spec(spec_mgr)

            # Inject dependencies for the manager module
            import sys
            sys.modules["helpers.openbao_client"] = client_mod
            sys.modules["helpers.config"] = config_mod

            spec_mgr.loader.exec_module(mgr_mod)

            _manager = mgr_mod.OpenBaoSecretsManager.get_or_create(
                config, DEFAULT_SECRETS_FILE
            )

            # ALWAYS return the manager when enabled+configured.
            # The manager handles fallback_to_env internally:
            #   - True:  load_secrets() falls back to .env on OpenBao failure
            #   - False: load_secrets() returns empty dict on OpenBao failure
            if _manager.is_available():
                logger.info("OpenBao secrets manager active (connected)")
            else:
                if config.fallback_to_env:
                    logger.warning(
                        "OpenBao unavailable — manager will use .env fallback"
                    )
                else:
                    logger.warning(
                        "OpenBao unavailable and fallback_to_env=False — "
                        "secrets will be empty until OpenBao recovers"
                    )
            return _manager

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
