import os

from python.helpers.life_events import emit_event
from instruments.custom.life_os.life_db import LifeOSDatabase


def test_emit_event_writes_life_os(tmp_path):
    db_path = os.path.join(tmp_path, "life_os.db")
    emit_event("workflow.execution_started", {"execution_id": 1}, db_path=db_path)

    db = LifeOSDatabase(db_path)
    events = db.list_events(limit=5)
    assert len(events) == 1
    assert events[0]["type"] == "workflow.execution_started"
