from python.helpers.api import ApiHandler, Input, Output, Request
from python.helpers import branding


class BrandingGet(ApiHandler):
    """Return branding configuration for the frontend."""

    @classmethod
    def requires_auth(cls) -> bool:
        return False

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET"]

    async def process(self, input: Input, request: Request) -> Output:
        return {
            "name": branding.BRAND_NAME,
            "slug": branding.BRAND_SLUG,
            "url": branding.BRAND_URL,
            "github_url": branding.BRAND_GITHUB_URL,
        }
