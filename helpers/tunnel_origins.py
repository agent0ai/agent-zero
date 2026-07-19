import json
import urllib.request
from urllib.parse import urlparse


_DEFAULT_PORTS = {
    "http": 80,
    "https": 443,
    "ws": 80,
    "wss": 443,
}


def origin_from_url(value):
    """Normalize a URL or Origin header to scheme://host[:port]."""
    if not isinstance(value, str) or not value.strip():
        return None
    parsed = urlparse(value.strip())
    if not parsed.scheme or not parsed.hostname:
        return None

    scheme = parsed.scheme.lower()
    host = parsed.hostname.lower()
    try:
        port = parsed.port
    except ValueError:
        return None

    origin = f"{scheme}://{host}"
    if port and port != _DEFAULT_PORTS.get(scheme):
        origin += f":{port}"
    return origin


def origin_key(value):
    """Return a comparable same-origin tuple including default ports."""
    origin = origin_from_url(value)
    if not origin:
        return None
    parsed = urlparse(origin)
    try:
        port = parsed.port or _DEFAULT_PORTS.get(parsed.scheme)
    except ValueError:
        return None
    if not parsed.scheme or not parsed.hostname or port is None:
        return None
    return parsed.scheme, parsed.hostname.lower(), int(port)


def get_active_tunnel_origins():
    """Return normalized origins for currently active Remote Control URLs."""
    origins = []

    try:
        from helpers.tunnel_manager import TunnelManager

        tunnel_url = TunnelManager.get_instance().get_tunnel_url()
        _append_origin(origins, tunnel_url)
    except Exception:
        pass

    try:
        _append_origin(origins, _get_tunnel_service_url())
    except Exception:
        pass

    return origins


def _append_origin(origins, url):
    origin = origin_from_url(url)
    if origin and origin not in origins:
        origins.append(origin)


def _get_tunnel_service_url():
    try:
        from helpers import dotenv, runtime

        should_query_service = bool(
            runtime.is_dockerized()
            or runtime.get_arg("tunnel_api_port")
            or dotenv.get_dotenv_value("TUNNEL_API_PORT")
        )
        if not should_query_service:
            return None

        port = runtime.get_tunnel_api_port()
    except Exception:
        return None

    body = json.dumps({"action": "get"}).encode("utf-8")
    request = urllib.request.Request(
        f"http://localhost:{port}/",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=0.35) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
    except Exception:
        return None

    if isinstance(payload, dict) and payload.get("success"):
        return payload.get("tunnel_url")
    return None
