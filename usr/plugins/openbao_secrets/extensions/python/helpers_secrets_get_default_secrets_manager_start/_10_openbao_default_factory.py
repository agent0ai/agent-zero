"""OpenBao factory extension for framework settings secret access.

Intercepts get_default_secrets_manager() via @extensible to return
OpenBaoSecretsManager when OpenBao is configured and available.
"""
import logging
from python.helpers.extension import Extension

logger = logging.getLogger(__name__)


class OpenBaoDefaultFactory(Extension):
    """Replace default SecretsManager with OpenBao-backed manager.

    This extension is sync-only (get_default_secrets_manager is sync).
    self.agent may be None since the function receives AgentContext, not Agent.
    """

    def execute(self, **kwargs) -> None:
        data = kwargs.get("data", {})

        try:
            manager = self._get_openbao_manager()
            if manager is not None:
                data["result"] = manager  # Short-circuit the original function
        except Exception as exc:
            logger.debug("OpenBao factory extension skipped: %s", exc)

    def _get_openbao_manager(self):
        """Lazily load and return the OpenBao manager singleton."""
        import importlib.util
        import os
        from python.helpers.plugins import find_plugin_dir

        plugin_dir = find_plugin_dir("openbao_secrets")
        if not plugin_dir:
            return None

        # Dynamically import factory_common from the plugin directory
        fc_path = os.path.join(plugin_dir, "helpers", "factory_common.py")
        if not os.path.exists(fc_path):
            return None

        spec = importlib.util.spec_from_file_location(
            "openbao_secrets_factory_common", fc_path
        )
        fc_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fc_mod)

        return fc_mod.get_openbao_manager()
