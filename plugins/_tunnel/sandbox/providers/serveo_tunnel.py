from flaredantic import ServeoConfig, ServeoTunnel

from .tunnel_common import FlaredanticTunnelHelper


class ServeoTunnelHelper(FlaredanticTunnelHelper):
    label = "Serveo"

    def build_tunnel(self):
        config = ServeoConfig(port=self.port)
        return ServeoTunnel(config)
