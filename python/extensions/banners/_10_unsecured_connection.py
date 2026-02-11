import re

from python.helpers import branding, dotenv
from python.helpers.extension import Extension


class UnsecuredConnectionCheck(Extension):
    """Check: non-local without credentials, or credentials over non-HTTPS."""

    async def execute(self, banners: list = [], frontend_context: dict = {}, **kwargs):
        hostname = frontend_context.get("hostname", "")
        protocol = frontend_context.get("protocol", "")

        auth_login = dotenv.get_dotenv_value(dotenv.KEY_AUTH_LOGIN, "")
        auth_password = dotenv.get_dotenv_value(dotenv.KEY_AUTH_PASSWORD, "")
        has_credentials = bool(
            auth_login
            and auth_login.strip()
            and auth_password
            and auth_password.strip()
        )

        is_local = self._is_localhost(hostname)
        is_https = protocol == "https:"

        if not is_local and not has_credentials:
            banners.append(
                {
                    "id": "unsecured-connection",
                    "type": "warning",
                    "priority": 80,
                    "title": "Unsecured Connection",
                    "html": f"""You are accessing {branding.BRAND_NAME} from a non-local address without authentication.
                         <a href="#" onclick="document.getElementById('settings').click(); return false;">
                         Configure credentials</a> in Settings → External Services → Authentication.""",
                    "dismissible": True,
                    "source": "backend",
                }
            )

        if has_credentials and not is_local and not is_https:
            banners.append(
                {
                    "id": "credentials-unencrypted",
                    "type": "warning",
                    "priority": 90,
                    "title": "Credentials May Be Sent Unencrypted",
                    "html": """Your connection is not using HTTPS. Login credentials may be transmitted in plain text.
                         Consider using HTTPS or a secure tunnel.""",
                    "dismissible": True,
                    "source": "backend",
                }
            )

    def _is_localhost(self, hostname: str) -> bool:
        local_patterns = ["localhost", "127.0.0.1", "::1", "0.0.0.0"]

        if hostname in local_patterns:
            return True

        # RFC1918 private ranges
        if re.match(r"^192\.168\.\d{1,3}\.\d{1,3}$", hostname):
            return True
        if re.match(r"^10\.\d{1,3}\.\d{1,3}\.\d{1,3}$", hostname):
            return True
        if re.match(r"^172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}$", hostname):
            return True

        # .local domains
        if hostname.endswith(".local"):
            return True

        return False
