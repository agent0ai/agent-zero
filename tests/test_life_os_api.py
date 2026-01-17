import json
from types import SimpleNamespace

from python.api.life_os_dashboard import LifeOsDashboard


class DummyRequest:
    def __init__(self, payload):
        self._payload = payload
        self.is_json = True
        self.data = json.dumps(payload).encode("utf-8")

    def get_json(self):
        return self._payload


async def test_life_os_dashboard_api(tmp_path, monkeypatch):
    from instruments.custom.life_os.life_db import LifeOSDatabase
    from python.helpers import files

    db_path = tmp_path / "life_os.db"
    LifeOSDatabase(str(db_path)).add_event("workflow.execution_started", {"execution_id": 1})

    monkeypatch.setattr(files, "get_abs_path", lambda path: str(db_path))

    handler = LifeOsDashboard(SimpleNamespace(), SimpleNamespace())
    result = await handler.process({}, DummyRequest({}))

    assert result["success"] is True
    assert result["dashboard"]["event_count"] >= 1
