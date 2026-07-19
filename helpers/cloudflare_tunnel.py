from flaredantic import FlareConfig, FlareTunnel

from helpers.tunnel_common import FlaredanticTunnelHelper


class CloudflareTunnel(FlaredanticTunnelHelper):
    label = "Cloudflare Tunnel"

    def build_tunnel(self):
        config = FlareConfig(port=self.port, verbose=True)
        return FlareTunnel(config)
