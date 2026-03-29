import sys
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers.ws import WsHandler, _SecurityContext, _check_security


# Handler variants with different security flag combinations

class _OpenHandler(WsHandler):
    @classmethod
    def requires_auth(cls) -> bool:
        return False

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, event, data, sid):
        return None


class _AuthOnlyHandler(WsHandler):
    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, event, data, sid):
        return None


class _CsrfHandler(WsHandler):
    """Default: requires_auth=True, requires_csrf=True (via default)."""

    async def process(self, event, data, sid):
        return None


class _LoopbackHandler(WsHandler):
    @classmethod
    def requires_loopback(cls) -> bool:
        return True

    @classmethod
    def requires_auth(cls) -> bool:
        return False

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, event, data, sid):
        return None


class _ApiKeyHandler(WsHandler):
    @classmethod
    def requires_api_key(cls) -> bool:
        return True

    @classmethod
    def requires_auth(cls) -> bool:
        return False

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, event, data, sid):
        return None


# Helper to build _SecurityContext quickly

def _ctx(
    *,
    auth_hash=None,
    csrf_token="tok",
    client_csrf_token="tok",
    csrf_cookie="tok",
    remote_addr="127.0.0.1",
    api_key=None,
) -> _SecurityContext:
    return _SecurityContext(
        auth_hash=auth_hash,
        csrf_token=csrf_token,
        client_csrf_token=client_csrf_token,
        csrf_cookie=csrf_cookie,
        remote_addr=remote_addr,
        api_key=api_key,
    )


# Open handler (no security)

def test_open_handler_always_passes():
    assert _check_security(_OpenHandler, _ctx()) is None


def test_open_handler_passes_even_without_tokens():
    assert _check_security(_OpenHandler, _ctx(csrf_token=None, client_csrf_token=None, csrf_cookie=None)) is None


# Loopback

def test_loopback_allows_127_0_0_1():
    assert _check_security(_LoopbackHandler, _ctx(remote_addr="127.0.0.1")) is None


def test_loopback_allows_ipv6():
    assert _check_security(_LoopbackHandler, _ctx(remote_addr="::1")) is None


def test_loopback_rejects_remote():
    result = _check_security(_LoopbackHandler, _ctx(remote_addr="192.168.1.50"))
    assert result is not None
    assert result["code"] == "FORBIDDEN"


def test_loopback_rejects_none():
    result = _check_security(_LoopbackHandler, _ctx(remote_addr=None))
    assert result is not None
    assert result["code"] == "FORBIDDEN"


# Auth

@patch("helpers.login.get_credentials_hash", return_value="hashed123")
def test_auth_passes_with_matching_hash(_mock):
    result = _check_security(_AuthOnlyHandler, _ctx(auth_hash="hashed123"))
    assert result is None


@patch("helpers.login.get_credentials_hash", return_value="hashed123")
def test_auth_rejects_wrong_hash(_mock):
    result = _check_security(_AuthOnlyHandler, _ctx(auth_hash="wrong"))
    assert result is not None
    assert result["code"] == "AUTH_REQUIRED"


@patch("helpers.login.get_credentials_hash", return_value="hashed123")
def test_auth_rejects_missing_hash(_mock):
    result = _check_security(_AuthOnlyHandler, _ctx(auth_hash=None))
    assert result is not None
    assert result["code"] == "AUTH_REQUIRED"


@patch("helpers.login.get_credentials_hash", return_value=None)
def test_auth_passes_when_no_credentials_configured(_mock):
    """When no password is set (get_credentials_hash returns None/empty),
    auth check should pass regardless of the client hash."""
    result = _check_security(_AuthOnlyHandler, _ctx(auth_hash=None))
    assert result is None


# CSRF

@patch("helpers.login.get_credentials_hash", return_value=None)
def test_csrf_passes_with_all_tokens_matching(_mock):
    result = _check_security(_CsrfHandler, _ctx(csrf_token="abc", client_csrf_token="abc", csrf_cookie="abc"))
    assert result is None


@patch("helpers.login.get_credentials_hash", return_value=None)
def test_csrf_rejects_missing_server_token(_mock):
    result = _check_security(_CsrfHandler, _ctx(csrf_token=None, client_csrf_token="abc", csrf_cookie="abc"))
    assert result is not None
    assert result["code"] == "CSRF_MISSING"


@patch("helpers.login.get_credentials_hash", return_value=None)
def test_csrf_rejects_missing_client_token(_mock):
    result = _check_security(_CsrfHandler, _ctx(csrf_token="abc", client_csrf_token=None, csrf_cookie="abc"))
    assert result is not None
    assert result["code"] == "CSRF_INVALID"


@patch("helpers.login.get_credentials_hash", return_value=None)
def test_csrf_rejects_mismatched_client_token(_mock):
    result = _check_security(_CsrfHandler, _ctx(csrf_token="abc", client_csrf_token="xyz", csrf_cookie="abc"))
    assert result is not None
    assert result["code"] == "CSRF_INVALID"


@patch("helpers.login.get_credentials_hash", return_value=None)
def test_csrf_rejects_mismatched_cookie(_mock):
    result = _check_security(_CsrfHandler, _ctx(csrf_token="abc", client_csrf_token="abc", csrf_cookie="wrong"))
    assert result is not None
    assert result["code"] == "CSRF_COOKIE"


# API Key

@patch("helpers.settings.get_settings", return_value={"mcp_server_token": "secret-key-123"})
def test_api_key_passes_with_correct_key(_mock):
    result = _check_security(_ApiKeyHandler, _ctx(api_key="secret-key-123"))
    assert result is None


@patch("helpers.settings.get_settings", return_value={"mcp_server_token": "secret-key-123"})
def test_api_key_rejects_wrong_key(_mock):
    result = _check_security(_ApiKeyHandler, _ctx(api_key="wrong-key"))
    assert result is not None
    assert result["code"] == "API_KEY_REQUIRED"


@patch("helpers.settings.get_settings", return_value={"mcp_server_token": "secret-key-123"})
def test_api_key_rejects_missing_key(_mock):
    result = _check_security(_ApiKeyHandler, _ctx(api_key=None))
    assert result is not None
    assert result["code"] == "API_KEY_REQUIRED"


# Combined flags

class _FullSecurityHandler(WsHandler):
    @classmethod
    def requires_loopback(cls) -> bool:
        return True

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_api_key(cls) -> bool:
        return True

    async def process(self, event, data, sid):
        return None


@patch("helpers.login.get_credentials_hash", return_value="hash")
@patch("helpers.settings.get_settings", return_value={"mcp_server_token": "key"})
def test_full_security_passes_when_all_match(_mock_settings, _mock_login):
    result = _check_security(
        _FullSecurityHandler,
        _ctx(
            remote_addr="127.0.0.1",
            auth_hash="hash",
            csrf_token="tok",
            client_csrf_token="tok",
            csrf_cookie="tok",
            api_key="key",
        ),
    )
    assert result is None


@patch("helpers.login.get_credentials_hash", return_value="hash")
@patch("helpers.settings.get_settings", return_value={"mcp_server_token": "key"})
def test_full_security_fails_at_first_check_loopback(_mock_settings, _mock_login):
    """Loopback check runs first; if it fails, later checks don't matter."""
    result = _check_security(
        _FullSecurityHandler,
        _ctx(
            remote_addr="10.0.0.1",
            auth_hash="hash",
            csrf_token="tok",
            client_csrf_token="tok",
            csrf_cookie="tok",
            api_key="key",
        ),
    )
    assert result is not None
    assert result["code"] == "FORBIDDEN"
