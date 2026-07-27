"""SSRF guard — refuse outbound fetches aimed at the infrastructure, not the internet.

Patch for CVE-2026-4308. The document fetcher accepted any URI and handed it straight to
aiohttp with ``allow_redirects=True``, so a document URL (which an agent will happily take
from a web page it just read) could reach:

* the loopback interface — other services on the same host,
* link-local 169.254.169.254 — cloud instance metadata, i.e. credentials,
* RFC1918 ranges — anything else on the private network,
* and via a redirect, all of the above starting from a perfectly public-looking URL.

This module is the single decision point for "may we fetch this?". It is deliberately
stdlib-only and deny-by-default: a hostname must resolve, and **every** address it
resolves to must be a global unicast address, or the fetch is refused.

Redirects are validated per hop by the caller (see fetch.py) rather than delegated to the
HTTP client, because a redirect is just another attacker-chosen URL.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

ALLOWED_SCHEMES = frozenset({"http", "https"})
MAX_REDIRECTS = 3


class BlockedRequestError(ValueError):
    """The requested URL points at non-public infrastructure and was refused."""


def _addresses_for(host: str) -> list:
    """Every address the hostname resolves to (A + AAAA). Raises if it resolves to none."""
    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise BlockedRequestError(f"host does not resolve: {host}") from exc
    addresses = []
    for info in infos:
        sockaddr = info[4]
        try:
            addresses.append(ipaddress.ip_address(sockaddr[0]))
        except ValueError:
            continue
    if not addresses:
        raise BlockedRequestError(f"host resolved to no usable address: {host}")
    return addresses


def _is_public(address) -> bool:
    """Global unicast only. Rejects loopback, private, link-local, reserved, multicast.

    ``is_global`` alone is not enough: it does not exclude every reserved range on all
    Python versions, so the explicit checks stay as belt-and-braces.
    """
    if (
        address.is_loopback
        or address.is_private
        or address.is_link_local
        or address.is_reserved
        or address.is_multicast
        or address.is_unspecified
    ):
        return False
    # IPv4-mapped/compatible IPv6 (e.g. ::ffff:127.0.0.1) must be judged on the v4 value.
    mapped = getattr(address, "ipv4_mapped", None)
    if mapped is not None:
        return _is_public(mapped)
    sixtofour = getattr(address, "sixtofour", None)
    if sixtofour is not None:
        return _is_public(sixtofour)
    return bool(getattr(address, "is_global", True))


def assert_public_url(url: str) -> str:
    """Return the URL if it is safe to fetch; raise BlockedRequestError otherwise."""
    parsed = urlparse(url)
    scheme = (parsed.scheme or "").lower()
    if scheme not in ALLOWED_SCHEMES:
        raise BlockedRequestError(
            f"refused scheme {scheme or '(none)'}: only http/https may be fetched"
        )
    host = parsed.hostname
    if not host:
        raise BlockedRequestError("refused URL with no host")
    # A bare IP literal is checked directly; a name is checked on every resolved address.
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    addresses = [literal] if literal is not None else _addresses_for(host)
    for address in addresses:
        if not _is_public(address):
            raise BlockedRequestError(
                f"refused {host}: resolves to non-public address {address}"
            )
    return url


def is_public_url(url: str) -> bool:
    try:
        assert_public_url(url)
        return True
    except BlockedRequestError:
        return False
