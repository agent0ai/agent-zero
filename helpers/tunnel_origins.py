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
    """Discover the active plugin URL without starting any service."""
    try:
        from plugins._tunnel.helpers.runtime import status
        current = status()
        origin = origin_from_url(current.get("tunnel_url")) if current.get("is_running") else None
        return [origin] if origin else []
    except Exception:
        return []
