"""Tests for python/helpers/websocket.py."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --- normalize_origin ---


class TestNormalizeOrigin:
    def test_normalize_origin_valid_url(self):
        from python.helpers.websocket import normalize_origin

        assert normalize_origin("https://example.com") == "https://example.com"
        assert normalize_origin("http://localhost:3000") == "http://localhost:3000"
        assert normalize_origin("  https://app.example.com:8080  ") == "https://app.example.com:8080"

    def test_normalize_origin_returns_none_for_empty(self):
        from python.helpers.websocket import normalize_origin

        assert normalize_origin("") is None
        assert normalize_origin("   ") is None
        assert normalize_origin(None) is None

    def test_normalize_origin_returns_none_for_invalid(self):
        from python.helpers.websocket import normalize_origin

        assert normalize_origin("not-a-url") is None
        assert normalize_origin(123) is None


# --- validate_ws_origin ---


class TestValidateWsOrigin:
    def test_validate_ws_origin_missing_origin(self):
        from python.helpers.websocket import validate_ws_origin

        ok, err = validate_ws_origin({"HTTP_HOST": "localhost:5000"})
        assert not ok
        assert err == "missing_origin"

    def test_validate_ws_origin_matching_origin_and_host(self):
        from python.helpers.websocket import validate_ws_origin

        environ = {
            "HTTP_ORIGIN": "http://localhost:5000",
            "HTTP_HOST": "localhost:5000",
        }
        ok, err = validate_ws_origin(environ)
        assert ok
        assert err is None

    def test_validate_ws_origin_host_mismatch(self):
        from python.helpers.websocket import validate_ws_origin

        environ = {
            "HTTP_ORIGIN": "http://evil.com",
            "HTTP_HOST": "localhost:5000",
        }
        ok, err = validate_ws_origin(environ)
        assert not ok
        assert err in ("origin_host_mismatch", "origin_port_mismatch")

    def test_validate_ws_origin_uses_referer_when_origin_missing(self):
        from python.helpers.websocket import validate_ws_origin

        environ = {
            "HTTP_REFERER": "http://localhost:5000",
            "HTTP_HOST": "localhost:5000",
        }
        ok, err = validate_ws_origin(environ)
        assert ok
        assert err is None

    def test_validate_ws_origin_forwarded_headers(self):
        from python.helpers.websocket import validate_ws_origin

        environ = {
            "HTTP_ORIGIN": "https://app.example.com",
            "HTTP_X_FORWARDED_HOST": "app.example.com",
            "HTTP_X_FORWARDED_PROTO": "https",
        }
        ok, err = validate_ws_origin(environ)
        assert ok
        assert err is None


# --- WebSocketResult ---


class TestWebSocketResult:
    def test_ok_creates_success_result(self):
        from python.helpers.websocket import WebSocketResult

        r = WebSocketResult.ok(data={"foo": "bar"})
        assert r._ok is True
        assert r._data == {"foo": "bar"}
        assert r._error is None

    def test_ok_with_correlation_id_and_duration(self):
        from python.helpers.websocket import WebSocketResult

        r = WebSocketResult.ok(
            data={"x": 1},
            correlation_id="cid-123",
            duration_ms=42.5,
        )
        assert r._correlation_id == "cid-123"
        assert r._duration_ms == 42.5

    def test_error_creates_error_result(self):
        from python.helpers.websocket import WebSocketResult

        r = WebSocketResult.error(code="NOT_FOUND", message="Resource not found")
        assert r._ok is False
        assert r._error == {"code": "NOT_FOUND", "error": "Resource not found"}

    def test_error_with_details(self):
        from python.helpers.websocket import WebSocketResult

        r = WebSocketResult.error(
            code="VALIDATION",
            message="Invalid input",
            details={"field": "email"},
        )
        assert r._error["details"] == {"field": "email"}

    def test_error_rejects_empty_code(self):
        from python.helpers.websocket import WebSocketResult

        with pytest.raises(ValueError, match="Error code"):
            WebSocketResult.error(code="", message="msg")

    def test_error_rejects_empty_message(self):
        from python.helpers.websocket import WebSocketResult

        with pytest.raises(ValueError, match="Error message"):
            WebSocketResult.error(code="ERR", message="")

    def test_init_rejects_ok_with_error(self):
        from python.helpers.websocket import WebSocketResult

        with pytest.raises(ValueError, match="both ok and have an error"):
            WebSocketResult(ok=True, error={"code": "x", "error": "y"})

    def test_init_rejects_not_ok_without_error(self):
        from python.helpers.websocket import WebSocketResult

        with pytest.raises(ValueError, match="either be ok or have an error"):
            WebSocketResult(ok=False)

    def test_as_result_produces_canonical_shape(self):
        from python.helpers.websocket import WebSocketResult

        r = WebSocketResult.ok(data={"result": 42}, correlation_id="c1")
        out = r.as_result(handler_id="handler1", fallback_correlation_id="fallback")
        assert out["handlerId"] == "handler1"
        assert out["ok"] is True
        assert out["data"] == {"result": 42}
        assert out["correlationId"] == "c1"

    def test_as_result_uses_fallback_correlation_id(self):
        from python.helpers.websocket import WebSocketResult

        r = WebSocketResult.ok(data={})
        out = r.as_result(handler_id="h", fallback_correlation_id="fb")
        assert out["correlationId"] == "fb"

    def test_as_result_includes_duration_ms(self):
        from python.helpers.websocket import WebSocketResult

        r = WebSocketResult.ok(data={}, duration_ms=12.3456)
        out = r.as_result(handler_id="h", fallback_correlation_id=None)
        assert "durationMs" in out
        assert out["durationMs"] == 12.3456


# --- WebSocketHandler ---


class TestWebSocketHandler:
    def test_validate_event_types_accepts_valid(self):
        from python.helpers.websocket import WebSocketHandler

        class DummyHandler(WebSocketHandler):
            @classmethod
            def get_event_types(cls):
                return ["my_event", "another_event"]

        validated = DummyHandler.validate_event_types(["my_event", "another_event"])
        assert validated == ["my_event", "another_event"]

    def test_validate_event_types_rejects_reserved(self):
        from python.helpers.websocket import WebSocketHandler

        class DummyHandler(WebSocketHandler):
            @classmethod
            def get_event_types(cls):
                return []

        with pytest.raises(ValueError, match="reserved"):
            DummyHandler.validate_event_types(["connect"])

    def test_validate_event_types_rejects_invalid_format(self):
        from python.helpers.websocket import WebSocketHandler

        class DummyHandler(WebSocketHandler):
            @classmethod
            def get_event_types(cls):
                return []

        with pytest.raises(ValueError, match="lowercase_snake_case"):
            DummyHandler.validate_event_types(["InvalidEvent"])

    def test_validate_event_types_rejects_duplicates(self):
        from python.helpers.websocket import WebSocketHandler

        class DummyHandler(WebSocketHandler):
            @classmethod
            def get_event_types(cls):
                return []

        with pytest.raises(ValueError, match="Duplicate"):
            DummyHandler.validate_event_types(["foo", "foo"])

    def test_validate_event_types_requires_at_least_one(self):
        from python.helpers.websocket import WebSocketHandler

        class DummyHandler(WebSocketHandler):
            @classmethod
            def get_event_types(cls):
                return []

        with pytest.raises(ValueError, match="at least one"):
            DummyHandler.validate_event_types([])

    def test_requires_auth_default_true(self):
        from python.helpers.websocket import WebSocketHandler

        class DummyHandler(WebSocketHandler):
            @classmethod
            def get_event_types(cls):
                return ["x"]

        assert DummyHandler.requires_auth() is True

    def test_requires_csrf_mirrors_requires_auth(self):
        from python.helpers.websocket import WebSocketHandler

        class DummyHandler(WebSocketHandler):
            @classmethod
            def get_event_types(cls):
                return ["x"]

        assert DummyHandler.requires_csrf() == DummyHandler.requires_auth()


# --- ConnectionNotFoundError ---


class TestConnectionNotFoundError:
    def test_connection_not_found_error_with_namespace(self):
        from python.helpers.websocket import ConnectionNotFoundError

        e = ConnectionNotFoundError("sid-1", namespace="/ns")
        assert e.sid == "sid-1"
        assert e.namespace == "/ns"
        assert "namespace" in str(e)
        assert "sid-1" in str(e)

    def test_connection_not_found_error_without_namespace(self):
        from python.helpers.websocket import ConnectionNotFoundError

        e = ConnectionNotFoundError("sid-2")
        assert e.sid == "sid-2"
        assert e.namespace is None
        assert "sid-2" in str(e)


# --- SingletonInstantiationError ---


class TestSingletonInstantiationError:
    def test_singleton_instantiation_error(self):
        from python.helpers.websocket import SingletonInstantiationError

        e = SingletonInstantiationError("Custom message")
        assert "Custom message" in str(e)
