from helpers.extension import Extension
from plugins._tunnel.helpers import runtime


class RequireTunnelAuth(Extension):
    def execute(self, **kwargs):
        # Run before sandbox restoration so an old tunnel cannot resume without sign-in.
        if not runtime.auth_configured():
            runtime.stop()
