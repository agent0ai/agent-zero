"""Non-Cloudflare provider adapter. File status only; no HTTP control server."""
import json
import os
from pathlib import Path
import signal
import sys
import threading

from providers.tunnel_manager import TunnelManager


def main():
    manager = TunnelManager.get_instance()
    stopped = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stopped.set())
    signal.signal(signal.SIGINT, lambda *_: stopped.set())
    thread = threading.Thread(target=manager.start_tunnel, args=(int(sys.argv[2]), sys.argv[1]), daemon=True)
    thread.start()
    output = Path('/var/lib/a0-tunnel/status.json')
    try:
        while not stopped.wait(0.5):
            payload = {'tunnel_url': manager.get_tunnel_url(), 'is_running': manager.is_running,
                       'notifications': list(manager.notifications), 'message': manager.get_last_error()}
            temporary = output.with_suffix('.tmp')
            temporary.write_text(json.dumps(payload))
            os.replace(temporary, output)
            if not thread.is_alive() and not manager.is_running:
                return 1
    finally:
        manager.stop_tunnel()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
