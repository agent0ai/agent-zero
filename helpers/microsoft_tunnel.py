import getpass
import hashlib
import os
import socket

from flaredantic import MicrosoftConfig, MicrosoftTunnel, NotifyEvent

try:
    from flaredantic.core.exceptions import MicrosoftTunnelError
except Exception:  # pragma: no cover - keeps tests independent from package internals
    MicrosoftTunnelError = RuntimeError

from helpers import files
from helpers.tunnel_common import FlaredanticTunnelHelper


MICROSOFT_TUNNEL_ID_ENV_KEYS = (
    "A0_MICROSOFT_DEV_TUNNEL_ID",
    "MICROSOFT_DEV_TUNNEL_ID",
)
MICROSOFT_TUNNEL_TIMEOUT = 120


def default_microsoft_tunnel_id():
    for env_key in MICROSOFT_TUNNEL_ID_ENV_KEYS:
        configured = (os.environ.get(env_key) or "").strip()
        if configured:
            return configured

    seed = "|".join([
        getpass.getuser(),
        socket.gethostname(),
        files.get_abs_path("usr"),
    ])
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:10]
    return f"agent-zero-{digest}"


class AgentZeroMicrosoftTunnel(MicrosoftTunnel):
    def notify(self, event, message, data=None):
        try:
            return super().notify(event, message, data)
        except AttributeError:
            self.agent_zero_notifications.append({
                "event": event.value if hasattr(event, "value") else event,
                "message": message,
                "data": data,
            })
            return None

    @property
    def agent_zero_notifications(self):
        if not hasattr(self, "_agent_zero_notifications"):
            self._agent_zero_notifications = []
        return self._agent_zero_notifications

    def _notify_progress(self, message, data=None):
        self.notify(NotifyEvent.INFO, message, data)

    def _ensure_logged_in(self):
        parent = getattr(super(), "_ensure_logged_in", None)
        if callable(parent):
            parent()
        self._notify_progress(
            "Microsoft Dev Tunnels login confirmed. Preparing your tunnel..."
        )

    def _ensure_tunnel(self):
        tunnel_id = self.config.tunnel_id
        port = str(self.config.port)

        self._notify_progress(
            f"Checking Microsoft Dev Tunnel `{tunnel_id}`...",
            {"tunnel_id": tunnel_id},
        )
        show = self._run_cmd(["show", tunnel_id])
        if show.returncode != 0:
            self._notify_progress(
                f"Creating Microsoft Dev Tunnel `{tunnel_id}`...",
                {"tunnel_id": tunnel_id},
            )
            create = self._run_cmd(["create", tunnel_id])
            if create.returncode != 0:
                raise MicrosoftTunnelError(f"Failed to create tunnel: {create.stdout}")
        else:
            self._notify_progress(
                f"Microsoft Dev Tunnel `{tunnel_id}` already exists. Checking port {port}...",
                {"tunnel_id": tunnel_id, "port": port},
            )

        self._notify_progress(
            f"Checking Microsoft Dev Tunnel port {port}...",
            {"tunnel_id": tunnel_id, "port": port},
        )
        port_show = self._run_cmd(["port", "show", tunnel_id, "-p", port])
        if port_show.returncode != 0:
            self._notify_progress(
                f"Creating Microsoft Dev Tunnel port {port}...",
                {"tunnel_id": tunnel_id, "port": port},
            )
            port_create = self._run_cmd([
                "port",
                "create",
                tunnel_id,
                "-p",
                port,
                "--protocol",
                "http",
            ])
            if port_create.returncode != 0:
                raise MicrosoftTunnelError(
                    f"Failed to create port: {port_create.stdout}"
                )

        self._notify_progress(
            "Microsoft Dev Tunnel setup is ready. Starting the secure host..."
        )


class MicrosoftDevTunnel(FlaredanticTunnelHelper):
    label = "Microsoft Dev Tunnels"

    def build_tunnel(self):
        config = MicrosoftConfig(
            port=self.port,
            verbose=True,
            timeout=MICROSOFT_TUNNEL_TIMEOUT,
            tunnel_id=default_microsoft_tunnel_id(),
        )
        return AgentZeroMicrosoftTunnel(config)

    def start(self):
        try:
            return super().start()
        except Exception as e:
            if "Timeout waiting for Microsoft Dev Tunnels URL" not in str(e):
                raise
            tunnel_id = default_microsoft_tunnel_id()
            raise RuntimeError(
                "Microsoft Dev Tunnels did not return a URL. Agent Zero uses "
                f"the tunnel id `{tunnel_id}` to avoid flaredantic's global "
                "`flaredantic` tunnel-id collision. If this still fails, set "
                "`A0_MICROSOFT_DEV_TUNNEL_ID` to a fresh unique value and try again."
            ) from e
