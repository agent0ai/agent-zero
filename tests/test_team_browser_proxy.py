import socket

import pytest

from helpers import team_surface_proxy


RESOLVER = "https://dns.example/dns-query"


def ipv4(address):
    return socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (address, 443)


@pytest.mark.parametrize("host, addresses", [
    ("private.example", ["127.0.0.1"]),
    ("private.example", ["192.168.0.80", "93.184.215.14"]),
    ("198.18.0.23", ["198.18.0.23"]),
])
def test_host_proxy_does_not_re_resolve_private_or_literal_targets(monkeypatch, host, addresses):
    monkeypatch.setattr(team_surface_proxy.socket, "getaddrinfo", lambda *_args, **_kw: list(map(ipv4, addresses)))

    def unexpected_lookup(*_args):
        pytest.fail("A private or literal address used the public resolver")

    monkeypatch.setattr(team_surface_proxy, "_resolve_public_dns", unexpected_lookup)
    with pytest.raises(ValueError, match="unavailable"):
        team_surface_proxy.public_address(host, 443, RESOLVER)


def test_host_proxy_connects_to_resolved_public_ip_not_synthetic_ip(monkeypatch):
    monkeypatch.setattr(team_surface_proxy.socket, "getaddrinfo", lambda *_args, **_kw: [ipv4("198.18.0.24")])
    resolved = [ipv4("93.184.215.14")]

    def lookup(host, port, resolver):
        assert (host, port, resolver) == ("public.example", 443, RESOLVER)
        return resolved

    monkeypatch.setattr(team_surface_proxy, "_resolve_public_dns", lookup)
    assert team_surface_proxy.public_address("public.example", 443, RESOLVER) == resolved[0]
    resolved[:] = [ipv4("192.168.0.80")]
    with pytest.raises(ValueError, match="unavailable"):
        team_surface_proxy.public_address("public.example", 443, RESOLVER)
