import os

from instruments.custom.life_os.life_manager import LifeOSManager


def test_life_os_events_and_plans(tmp_path):
    db_path = os.path.join(tmp_path, "life_os.db")
    manager = LifeOSManager(db_path)

    manager.emit_event("workflow.stage_changed", {"stage": "discovery"})
    manager.emit_event("calendar.event_created", {"title": "Kickoff"})

    dashboard = manager.get_dashboard()
    assert dashboard["event_count"] == 2
    assert dashboard["latest_event"]["type"] == "calendar.event_created"

    plan = manager.generate_daily_plan("2025-01-01")
    assert "2025-01-01" in plan["content"]
