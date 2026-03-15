"""Tests for python/helpers/state_snapshot.py."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --- validate_snapshot_schema_v1 ---


class TestValidateSnapshotSchemaV1:
    def test_validate_accepts_valid_snapshot(self):
        from python.helpers.state_snapshot import validate_snapshot_schema_v1

        snapshot = {
            "deselect_chat": False,
            "context": "",
            "contexts": [],
            "tasks": [],
            "logs": [],
            "log_guid": "",
            "log_version": 0,
            "log_progress": 0,
            "log_progress_active": False,
            "paused": False,
            "notifications": [],
            "notifications_guid": "",
            "notifications_version": 0,
        }
        validate_snapshot_schema_v1(snapshot)  # no raise

    def test_validate_rejects_non_dict(self):
        from python.helpers.state_snapshot import validate_snapshot_schema_v1

        with pytest.raises(TypeError, match="must be a dict"):
            validate_snapshot_schema_v1([])

    def test_validate_rejects_missing_keys(self):
        from python.helpers.state_snapshot import validate_snapshot_schema_v1

        snapshot = {"context": "", "logs": []}  # missing many keys
        with pytest.raises(ValueError, match="missing"):
            validate_snapshot_schema_v1(snapshot)

    def test_validate_rejects_extra_keys(self):
        from python.helpers.state_snapshot import validate_snapshot_schema_v1

        snapshot = {
            "deselect_chat": False,
            "context": "",
            "contexts": [],
            "tasks": [],
            "logs": [],
            "log_guid": "",
            "log_version": 0,
            "log_progress": 0,
            "log_progress_active": False,
            "paused": False,
            "notifications": [],
            "notifications_guid": "",
            "notifications_version": 0,
            "extra_key": "bad",
        }
        with pytest.raises(ValueError, match="unexpected"):
            validate_snapshot_schema_v1(snapshot)

    def test_validate_rejects_wrong_type_for_key(self):
        from python.helpers.state_snapshot import validate_snapshot_schema_v1

        snapshot = {
            "deselect_chat": False,
            "context": "",
            "contexts": "not_a_list",
            "tasks": [],
            "logs": [],
            "log_guid": "",
            "log_version": 0,
            "log_progress": 0,
            "log_progress_active": False,
            "paused": False,
            "notifications": [],
            "notifications_guid": "",
            "notifications_version": 0,
        }
        with pytest.raises(TypeError, match="contexts"):
            validate_snapshot_schema_v1(snapshot)


# --- parse_state_request_payload ---


class TestParseStateRequestPayload:
    def test_parse_valid_payload(self):
        from python.helpers.state_snapshot import parse_state_request_payload

        payload = {
            "context": "ctx-1",
            "log_from": 0,
            "notifications_from": 0,
            "timezone": "UTC",
        }
        req = parse_state_request_payload(payload)
        assert req.context == "ctx-1"
        assert req.log_from == 0
        assert req.notifications_from == 0
        assert req.timezone == "UTC"

    def test_parse_null_context(self):
        from python.helpers.state_snapshot import parse_state_request_payload

        payload = {
            "context": None,
            "log_from": 0,
            "notifications_from": 0,
            "timezone": "UTC",
        }
        req = parse_state_request_payload(payload)
        assert req.context is None

    def test_parse_rejects_invalid_context_type(self):
        from python.helpers.state_snapshot import parse_state_request_payload, StateRequestValidationError

        payload = {
            "context": 123,
            "log_from": 0,
            "notifications_from": 0,
            "timezone": "UTC",
        }
        with pytest.raises(StateRequestValidationError, match="context"):
            parse_state_request_payload(payload)

    def test_parse_rejects_negative_log_from(self):
        from python.helpers.state_snapshot import parse_state_request_payload, StateRequestValidationError

        payload = {
            "context": None,
            "log_from": -1,
            "notifications_from": 0,
            "timezone": "UTC",
        }
        with pytest.raises(StateRequestValidationError, match="log_from"):
            parse_state_request_payload(payload)

    def test_parse_rejects_empty_timezone(self):
        from python.helpers.state_snapshot import parse_state_request_payload, StateRequestValidationError

        payload = {
            "context": None,
            "log_from": 0,
            "notifications_from": 0,
            "timezone": "",
        }
        with pytest.raises(StateRequestValidationError, match="timezone"):
            parse_state_request_payload(payload)

    def test_parse_rejects_invalid_timezone(self):
        from python.helpers.state_snapshot import parse_state_request_payload, StateRequestValidationError

        payload = {
            "context": None,
            "log_from": 0,
            "notifications_from": 0,
            "timezone": "Invalid/Timezone",
        }
        with pytest.raises(StateRequestValidationError, match="timezone"):
            parse_state_request_payload(payload)


# --- StateRequestValidationError ---


class TestStateRequestValidationError:
    def test_state_request_validation_error_has_reason_and_details(self):
        from python.helpers.state_snapshot import StateRequestValidationError

        e = StateRequestValidationError(
            reason="test_reason",
            message="Test message",
            details={"key": "value"},
        )
        assert e.reason == "test_reason"
        assert str(e) == "Test message"
        assert e.details == {"key": "value"}


# --- _coerce_state_request_inputs ---


class TestCoerceStateRequestInputs:
    def test_coerce_uses_default_timezone_when_empty(self):
        from python.helpers.state_snapshot import _coerce_state_request_inputs

        with patch("python.helpers.state_snapshot.get_dotenv_value", return_value="Europe/London"):
            req = _coerce_state_request_inputs(
                context=None,
                log_from=0,
                notifications_from=0,
                timezone=None,
            )
            assert req.timezone == "Europe/London"

    def test_coerce_handles_non_int_log_from(self):
        from python.helpers.state_snapshot import _coerce_state_request_inputs

        with patch("python.helpers.state_snapshot.get_dotenv_value", return_value="UTC"):
            req = _coerce_state_request_inputs(
                context=None,
                log_from="invalid",
                notifications_from=0,
                timezone="UTC",
            )
            assert req.log_from == 0


# --- advance_state_request_after_snapshot ---


class TestAdvanceStateRequestAfterSnapshot:
    def test_advance_updates_log_from_from_snapshot(self):
        from python.helpers.state_snapshot import (
            StateRequestV1,
            advance_state_request_after_snapshot,
        )

        request = StateRequestV1(
            context="ctx",
            log_from=0,
            notifications_from=0,
            timezone="UTC",
        )
        snapshot = {"log_version": 5, "notifications_version": 3}
        result = advance_state_request_after_snapshot(request, snapshot)
        assert result.log_from == 5
        assert result.notifications_from == 3
        assert result.context == "ctx"
        assert result.timezone == "UTC"

    def test_advance_preserves_original_on_invalid_snapshot_values(self):
        from python.helpers.state_snapshot import (
            StateRequestV1,
            advance_state_request_after_snapshot,
        )

        request = StateRequestV1(
            context="ctx",
            log_from=10,
            notifications_from=20,
            timezone="UTC",
        )
        snapshot = {"log_version": "invalid", "notifications_version": "bad"}
        result = advance_state_request_after_snapshot(request, snapshot)
        assert result.log_from == 10
        assert result.notifications_from == 20


# --- build_snapshot, build_snapshot_from_request ---


@pytest.mark.asyncio
class TestBuildSnapshot:
    async def test_build_snapshot_from_request_produces_valid_schema(self):
        from python.helpers.state_snapshot import (
            StateRequestV1,
            build_snapshot_from_request,
            validate_snapshot_schema_v1,
        )

        mock_manager = MagicMock()
        mock_manager.output = MagicMock(return_value=[])
        mock_manager.guid = "guid"
        mock_manager.updates = []
        with patch("python.helpers.state_snapshot.AgentContext") as mock_ctx:
            mock_ctx.get = MagicMock(return_value=None)
            mock_ctx.all = MagicMock(return_value=[])
            with patch("python.helpers.state_snapshot.AgentContext.get_notification_manager", return_value=mock_manager):
                with patch("python.helpers.state_snapshot.TaskScheduler.get") as mock_ts:
                    mock_ts.return_value.get_task_by_uuid = MagicMock(return_value=None)
                    with patch("python.helpers.state_snapshot.Localization.get") as mock_loc:
                        mock_loc.return_value.set_timezone = MagicMock()

                        request = StateRequestV1(
                            context=None,
                            log_from=0,
                            notifications_from=0,
                            timezone="UTC",
                        )
                        snapshot = await build_snapshot_from_request(request=request)
                        validate_snapshot_schema_v1(snapshot)
                        assert "contexts" in snapshot
                        assert "tasks" in snapshot
                        assert "logs" in snapshot
                        assert "notifications" in snapshot
