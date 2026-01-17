import os

from instruments.custom.life_os.life_manager import LifeOSManager


def test_life_os_aggregates_sources(tmp_path):
    db_path = os.path.join(tmp_path, "life_os.db")
    manager = LifeOSManager(db_path)

    manager.emit_event("workflow.stage_changed", {"workflow": "alpha", "stage": "discovery"})
    manager.emit_event("scheduler.task_created", {"task": "Daily brief"})
    manager.emit_event("property.expense_recorded", {"property_id": 1, "amount": 120.0})

    dashboard = manager.get_dashboard()
    assert dashboard["event_count"] == 3
    assert dashboard["sources"]["workflow"] == 1
    assert dashboard["sources"]["scheduler"] == 1
    assert dashboard["sources"]["property"] == 1
