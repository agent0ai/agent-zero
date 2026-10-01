from datetime import datetime, timezone

from plugins._a0_acp.api.session import _session_payload


class _Context:
    id = "ctx-acp"
    name = "ACP"
    created_at = datetime(2026, 8, 16, tzinfo=timezone.utc)
    last_message = datetime(2026, 8, 16, 12, 34, tzinfo=timezone.utc)

    def get_data(self, key: str):
        return {"acp_cwd": "/workspace", "acp_mode": "default"}.get(key)


def test_session_payload_serializes_datetime_metadata() -> None:
    payload = _session_payload(_Context())

    assert payload["updated_at"] == "2026-08-16T12:34:00+00:00"
