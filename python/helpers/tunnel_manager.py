import threading
from collections import deque

from flaredantic import (
    FlareConfig,
    FlareTunnel,
    MicrosoftConfig,
    MicrosoftTunnel,
    NotifyData,
    NotifyEvent,
    ServeoConfig,
    ServeoTunnel,
    notifier,
)

from python.helpers.print_style import PrintStyle


# Singleton to manage the tunnel instance
class TunnelManager:
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def __init__(self):
        self.tunnel = None
        self.tunnel_url = None
        self.is_running = False
        self.provider = None
        self.notifications = deque(maxlen=50)
        self._subscribed = False

    def _on_notify(self, data: NotifyData):
        """Handle notifications from flaredantic"""
        self.notifications.append(
            {"event": data.event.value, "message": data.message, "data": data.data}
        )

    def _ensure_subscribed(self):
        """Subscribe to flaredantic notifications if not already"""
        if not self._subscribed:
            notifier.subscribe(self._on_notify)
            self._subscribed = True

    def get_notifications(self):
        """Get and clear pending notifications"""
        notifications = list(self.notifications)
        self.notifications.clear()
        return notifications

    def get_last_error(self):
        """Check for recent error in notifications without clearing"""
        for n in reversed(list(self.notifications)):
            if n["event"] == NotifyEvent.ERROR.value:
                return n["message"]
        return None

    def start_tunnel(self, port=80, provider="serveo"):
        """Start a new tunnel or return the existing one's URL"""
        if self.is_running and self.tunnel_url:
            return self.tunnel_url

        self.provider = provider
        self._ensure_subscribed()
        self.notifications.clear()

        try:
            # Start tunnel in a separate thread to avoid blocking
            def run_tunnel():
                try:
                    if self.provider == "cloudflared":
                        config = FlareConfig(port=port, verbose=True)
                        self.tunnel = FlareTunnel(config)
                    elif self.provider == "microsoft":
                        config = MicrosoftConfig(port=port, verbose=True)  # type: ignore
                        self.tunnel = MicrosoftTunnel(config)
                    else:  # Default to serveo
                        config = ServeoConfig(port=port)  # type: ignore
                        self.tunnel = ServeoTunnel(config)

                    self.tunnel.start()
                    self.tunnel_url = self.tunnel.tunnel_url
                    self.is_running = True
                except Exception as e:
                    error_msg = str(e)
                    PrintStyle.error(f"Error in tunnel thread: {error_msg}")
                    self.notifications.append(
                        {
                            "event": NotifyEvent.ERROR.value,
                            "message": error_msg,
                            "data": None,
                        }
                    )

            tunnel_thread = threading.Thread(target=run_tunnel)
            tunnel_thread.daemon = True
            tunnel_thread.start()

            # Wait for tunnel to start (no timeout - user may need time for login)
            import time

            while True:
                if self.tunnel_url:
                    break
                # Check if we have errors
                if any(
                    n["event"] == NotifyEvent.ERROR.value for n in self.notifications
                ):
                    break
                # Check if thread died without producing URL
                if not tunnel_thread.is_alive():
                    break
                time.sleep(0.1)

            return self.tunnel_url
        except Exception as e:
            PrintStyle.error(f"Error starting tunnel: {str(e)}")
            return None

    def stop_tunnel(self):
        """Stop the running tunnel"""
        if self.tunnel and self.is_running:
            try:
                self.tunnel.stop()
                self.is_running = False
                self.tunnel_url = None
                self.provider = None
                return True
            except Exception:
                return False
        return False

    def get_tunnel_url(self):
        """Get the current tunnel URL if available"""
        return self.tunnel_url if self.is_running else None
