"""Connect the team Browser's private Unix socket to the local HTTP proxy."""

import os
from pathlib import Path
import socket
from socketserver import BaseRequestHandler, ThreadingUnixStreamServer

from team_surface_proxy import relay_streams


def main():
    os.umask(0o177)
    endpoint = Path("/relay/proxy.sock")
    endpoint.unlink(missing_ok=True)
    port = int(os.environ["A0_TEAM_HOST_PROXY_PORT"])

    class HostProxy(BaseRequestHandler):
        def handle(self):
            try:
                self.request.settimeout(20)
                with socket.create_connection(("127.0.0.1", port), timeout=15) as upstream:
                    relay_streams(self.request, upstream)
            except OSError:
                pass

    with ThreadingUnixStreamServer(str(endpoint), HostProxy) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
