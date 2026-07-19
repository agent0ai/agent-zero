from flaredantic import NotifyEvent


def event_value(event):
    return event.value if hasattr(event, "value") else event


class TunnelHelper:
    def __init__(self, port, notify=None):
        self.port = port
        self.notify_callback = notify
        self.tunnel = None
        self.tunnel_url = None

    def _notify(self, event, message, data=None):
        if callable(self.notify_callback):
            self.notify_callback(event, message, data)

    def notify_starting(self, label):
        self._notify(
            NotifyEvent.CREATING_TUNNEL,
            f"Starting {label} on port {self.port}...",
        )

    def notify_url_ready(self, label, url):
        self._notify(
            NotifyEvent.TUNNEL_URL,
            f"{label} URL is ready",
            {"url": url},
        )

    def notify_stopped(self, label):
        self._notify(NotifyEvent.TUNNEL_STOPPED, f"{label} stopped")


class FlaredanticTunnelHelper(TunnelHelper):
    label = "Remote Control"

    def build_tunnel(self):
        raise NotImplementedError

    def start(self):
        self.notify_starting(self.label)
        self.tunnel = self.build_tunnel()
        self.tunnel.start()
        self.tunnel_url = getattr(self.tunnel, "tunnel_url", None)
        if self.tunnel_url:
            self.notify_url_ready(self.label, self.tunnel_url)
        return self.tunnel_url

    def stop(self):
        if self.tunnel:
            self.tunnel.stop()
        self.tunnel_url = None
        self.notify_stopped(self.label)
        return True
