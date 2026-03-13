"""Health check and connection test API for Deimos OpenBao plugin."""
import logging
from python.helpers.api import ApiHandler

logger = logging.getLogger(__name__)


class TestOpenbaoConnectionHandler(ApiHandler):
    """Handle test_openbao_connection action from plugin config UI."""

    async def handle(self, input: dict, request) -> dict:
        config_data = input.get("config", {})
        url = config_data.get("url", "http://127.0.0.1:8200")
        timeout = float(config_data.get("timeout", 10.0))
        tls_verify = config_data.get("tls_verify", True)
        tls_ca_cert = config_data.get("tls_ca_cert", "")

        try:
            import hvac

            verify = tls_ca_cert if tls_ca_cert else tls_verify
            client = hvac.Client(url=url, verify=verify, timeout=timeout)

            # Try health check (doesn't require authentication)
            health = client.sys.read_health_status(method="GET")

            if isinstance(health, dict):
                return {
                    "ok": True,
                    "data": {
                        "status": "healthy",
                        "initialized": health.get("initialized"),
                        "sealed": health.get("sealed"),
                        "standby": health.get("standby"),
                    },
                }
            else:
                return {"ok": True, "data": {"status": "reachable"}}

        except ImportError:
            return {"ok": False, "error": "hvac library not installed"}
        except Exception as exc:
            logger.debug("OpenBao connection test failed: %s", exc)
            return {"ok": False, "error": str(exc)}
