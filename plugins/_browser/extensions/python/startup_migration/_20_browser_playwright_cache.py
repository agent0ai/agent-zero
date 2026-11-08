from helpers import virtual_desktop_routes
from helpers.extension import Extension


class BrowserPlaywrightCacheMigration(Extension):
    def execute(self, **kwargs):
        virtual_desktop_routes.install_route_hooks()
