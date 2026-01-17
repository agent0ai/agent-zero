from typing import Any

from python.helpers import files
from instruments.custom.life_os.life_db import LifeOSDatabase


def emit_event(event_type: str, payload: dict[str, Any], db_path: str | None = None) -> dict[str, Any]:
    path = db_path or files.get_abs_path("./instruments/custom/life_os/data/life_os.db")
    db = LifeOSDatabase(path)
    event_id = db.add_event(event_type, payload)
    return {"id": event_id, "type": event_type, "payload": payload}
