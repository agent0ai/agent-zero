from helpers.extension import Extension
from helpers import virtual_desktop_routes


class DesktopStartup(Extension):
    def execute(self, **kwargs):
        virtual_desktop_routes.install_route_hooks()
