"""Regression tests for the two patched CVEs.

Each test states the exploit that worked against stock v2.6, then asserts it is refused.
Run: ./.venv-sec/bin/python -m pytest tests/test_security_patches.py -q
"""

from __future__ import annotations

import asyncio
import os

import pytest

from helpers import files
from helpers.net_guard import (
    BlockedRequestError,
    assert_public_url,
    is_public_url,
)


# --- CVE-2026-4307: path traversal / arbitrary file read -----------------------


def test_absolute_path_outside_base_is_refused():
    """Stock v2.6: get_abs_path('/etc/passwd') returned '/etc/passwd' verbatim."""
    with pytest.raises(files.PathEscapesBaseDirError):
        files.get_abs_path_contained("/etc/passwd")


def test_dotdot_traversal_is_refused():
    """Stock v2.6: os.path.join(base, '../../etc/passwd') walked straight out."""
    with pytest.raises(files.PathEscapesBaseDirError):
        files.get_abs_path_contained("../../etc/passwd")
    with pytest.raises(files.PathEscapesBaseDirError):
        files.get_abs_path_contained("usr/../../../etc/shadow")


def test_nested_traversal_is_refused():
    for candidate in (
        "tmp/../../../../root/.ssh/id_rsa",
        "./../../etc/hosts",
        "usr/uploads/../../../../etc/passwd",
    ):
        with pytest.raises(files.PathEscapesBaseDirError):
            files.get_abs_path_contained(candidate)


def test_legitimate_paths_still_resolve():
    """The guard must not simply break the feature."""
    inside = files.get_abs_path_contained("usr")
    assert inside.startswith(os.path.realpath(files.get_base_dir()))
    assert files.get_abs_path_contained(".") == os.path.realpath(files.get_base_dir())


def test_symlink_out_of_base_is_refused():
    """realpath() resolution means a symlink cannot be used as a side door."""
    base = os.path.realpath(files.get_base_dir())
    link = os.path.join(base, "tmp", "_pytest_escape_link")
    os.makedirs(os.path.dirname(link), exist_ok=True)
    if os.path.islink(link):
        os.unlink(link)
    os.symlink("/etc", link)
    try:
        with pytest.raises(files.PathEscapesBaseDirError):
            files.get_abs_path_contained("tmp/_pytest_escape_link/passwd")
    finally:
        os.unlink(link)


# --- CVE-2026-4308: SSRF --------------------------------------------------------


@pytest.mark.parametrize("url", [
    "http://127.0.0.1:8080/admin",
    "http://localhost/",
    "http://169.254.169.254/latest/meta-data/",      # cloud instance credentials
    "http://[::1]/",
    "http://0.0.0.0/",
    "http://10.0.0.5/internal",
    "http://192.168.1.1/router",
    "http://172.16.0.10/",
    "http://[::ffff:127.0.0.1]/",                    # IPv4-mapped IPv6 loopback
])
def test_private_and_loopback_targets_are_refused(url):
    """Stock v2.6 fetched every one of these with allow_redirects=True and no checks."""
    with pytest.raises(BlockedRequestError):
        assert_public_url(url)


@pytest.mark.parametrize("url", [
    "file:///etc/passwd",
    "gopher://127.0.0.1:11211/",
    "ftp://internal.host/secrets",
    "dict://127.0.0.1:11211/stat",
])
def test_non_http_schemes_are_refused(url):
    with pytest.raises(BlockedRequestError):
        assert_public_url(url)


@pytest.mark.parametrize("url", [
    "https://93.184.216.34/doc.pdf",    # public IPv4 literal
    "https://8.8.8.8/",                 # public IPv4 literal
    "https://[2606:4700:4700::1111]/",  # public IPv6 literal
])
def test_public_targets_are_allowed(url):
    """The guard must not over-block: real public addresses still pass.

    IP literals are used deliberately so this does not depend on DNS. Some sandboxed or
    proxied networks resolve every name into 198.18.0.0/15 (RFC 2544 benchmark space),
    which is correctly *not* public — a hostname assertion would fail there for
    environmental reasons rather than a logic error.
    """
    assert is_public_url(url) is True


def test_hostname_resolution_path_is_exercised():
    """Whatever a name resolves to, the verdict must match that address's class."""
    import ipaddress
    import socket

    try:
        resolved = socket.getaddrinfo("example.com", None)[0][4][0]
    except socket.gaierror:
        pytest.skip("no DNS in this environment")
    address = ipaddress.ip_address(resolved)
    expected_public = not (address.is_private or address.is_loopback)
    assert is_public_url("https://example.com/doc.pdf") is expected_public


def test_hostname_that_does_not_resolve_is_refused():
    with pytest.raises(BlockedRequestError):
        assert_public_url("https://this-host-should-not-exist.invalid/x")


def test_url_without_host_is_refused():
    with pytest.raises(BlockedRequestError):
        assert_public_url("http:///nohost")


def test_fetcher_refuses_a_blocked_target_without_retrying():
    """A refused target must raise immediately, not be retried and then masked as a
    generic 'Document fetch error' (which is what the shared retry path would do)."""
    from plugins._document_query.helpers.fetch import fetch_public_resource

    with pytest.raises(BlockedRequestError):
        asyncio.run(fetch_public_resource("http://169.254.169.254/latest/meta-data/"))


def test_fetch_no_longer_delegates_redirects():
    """Guard against the patch being reverted: allow_redirects=True must not return."""
    source = open("plugins/_document_query/helpers/fetch.py").read()
    assert "allow_redirects=True" not in source
    assert "allow_redirects=False" in source
    assert "assert_public_url" in source
