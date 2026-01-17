import threading
from typing import Optional


class TunnelWatchdog:
    _instance: Optional["TunnelWatchdog"] = None
    _lock = threading.Lock()

    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._interval = 60
        self._provider = "cloudflared"

    @classmethod
    def get_instance(cls) -> "TunnelWatchdog":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def start(self, interval: int = 60, provider: str = "cloudflared") -> None:
        if self._thread and self._thread.is_alive():
            return
        self._interval = max(15, int(interval))
        self._provider = provider
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    def status(self) -> dict:
        return {
            "running": bool(self._thread and self._thread.is_alive()),
            "interval": self._interval,
            "provider": self._provider,
        }

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                from python.helpers import tunnel_manager

                manager = tunnel_manager.TunnelManager.get_instance()
                if not manager.is_running or not manager.get_tunnel_url():
                    manager.start_tunnel(provider=self._provider)
            except Exception:
                pass
            self._stop_event.wait(self._interval)
