"""Tests for python/helpers/rfc.py."""

import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --- RFCInput & RFCCall ---


class TestRFCTypes:
    def test_rfc_input_structure(self):
        from python.helpers.rfc import RFCInput

        inp: RFCInput = {
            "module": "mymod",
            "function_name": "myfunc",
            "args": [1, 2],
            "kwargs": {"x": "y"},
        }
        assert inp["module"] == "mymod"
        assert inp["function_name"] == "myfunc"
        assert inp["args"] == [1, 2]
        assert inp["kwargs"] == {"x": "y"}

    def test_rfc_call_structure(self):
        from python.helpers.rfc import RFCCall

        call: RFCCall = {"rfc_input": "{}", "hash": "abc123"}
        assert call["rfc_input"] == "{}"
        assert call["hash"] == "abc123"


# --- call_rfc ---


@pytest.mark.asyncio
class TestCallRfc:
    async def test_call_rfc_sends_correct_payload(self):
        from python.helpers.rfc import call_rfc

        with patch("python.helpers.rfc._send_json_data", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"result": 42}
            result = await call_rfc(
                "http://localhost:3000",
                "password",
                "mymod",
                "myfunc",
                [1],
                {"k": "v"},
            )
            assert result == {"result": 42}
            mock_send.assert_called_once()
            call_data = mock_send.call_args[0][1]
            assert "rfc_input" in call_data
            assert "hash" in call_data
            inp = json.loads(call_data["rfc_input"])
            assert inp["module"] == "mymod"
            assert inp["function_name"] == "myfunc"
            assert inp["args"] == [1]
            assert inp["kwargs"] == {"k": "v"}

    async def test_call_rfc_raises_on_non_200(self):
        from python.helpers.rfc import call_rfc

        async def mock_send_fail(*args, **kwargs):
            raise Exception("Internal server error")

        with patch("python.helpers.rfc._send_json_data", side_effect=mock_send_fail):
            with pytest.raises(Exception, match="Internal server error"):
                await call_rfc("http://x", "p", "m", "f", [], {})


# --- handle_rfc ---


@pytest.mark.asyncio
class TestHandleRfc:
    async def test_handle_rfc_raises_on_invalid_hash(self):
        from python.helpers.rfc import handle_rfc, RFCCall

        call: RFCCall = {
            "rfc_input": json.dumps({"module": "m", "function_name": "f", "args": [], "kwargs": {}}),
            "hash": "invalid",
        }
        with patch("python.helpers.rfc.crypto.verify_data", return_value=False):
            with pytest.raises(Exception, match="Invalid RFC hash"):
                await handle_rfc(call, "password")

    async def test_handle_rfc_calls_function_on_valid_hash(self):
        from python.helpers.rfc import handle_rfc, RFCCall

        call: RFCCall = {
            "rfc_input": json.dumps({
                "module": "python.helpers.rfc",
                "function_name": "_get_function",
                "args": [],
                "kwargs": {"module": "json", "function_name": "dumps"},
            }),
            "hash": "will_be_verified",
        }
        with patch("python.helpers.rfc.crypto.verify_data", return_value=True):
            with patch("python.helpers.rfc._call_function") as mock_call:
                mock_call.return_value = "result"
                result = await handle_rfc(call, "password")
                assert result == "result"


# --- _get_function ---


class TestGetFunction:
    def test_get_function_returns_imported_function(self):
        from python.helpers.rfc import _get_function

        func = _get_function("json", "dumps")
        assert func == json.dumps

    def test_get_function_raises_for_nonexistent_module(self):
        from python.helpers.rfc import _get_function

        with pytest.raises(ModuleNotFoundError):
            _get_function("nonexistent_module_xyz", "func")

    def test_get_function_raises_for_nonexistent_attr(self):
        from python.helpers.rfc import _get_function

        with pytest.raises(AttributeError):
            _get_function("json", "nonexistent_func")


# --- _call_function (sync and async) ---


@pytest.mark.asyncio
class TestCallFunction:
    async def test_call_function_calls_sync(self):
        from python.helpers.rfc import _call_function

        result = await _call_function("json", "dumps", {"a": 1})
        assert result == '{"a": 1}'

    async def test_call_function_awaits_async(self):
        from python.helpers.rfc import _call_function

        async def async_func():
            return "async_result"

        async_mod = MagicMock()
        async_mod.async_func = async_func
        with patch("importlib.import_module", return_value=async_mod):
            result = await _call_function("async_mod", "async_func")
            assert result == "async_result"
