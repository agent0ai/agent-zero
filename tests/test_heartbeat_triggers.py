"""Tests for TriggerStore and trigger evaluation helpers."""

import pytest

from python.helpers.event_triggers import (
    HeartbeatTrigger,
    TriggerStore,
    TriggerType,
    evaluate_condition_trigger,
    evaluate_event_trigger,
    evaluate_message_trigger,
)


def _make_trigger(
    trigger_type: TriggerType = TriggerType.EVENT,
    config: dict | None = None,
    items: list | None = None,
    enabled: bool = True,
) -> HeartbeatTrigger:
    return HeartbeatTrigger.new(
        trigger_type=trigger_type,
        config=config or {},
        items=items or [],
        enabled=enabled,
    )


@pytest.mark.unit
class TestTriggerStore:
    def test_save_and_get(self):
        store = TriggerStore(":memory:")
        t = _make_trigger(config={"event_type": "test"})
        store.save(t)
        fetched = store.get(t.id)
        assert fetched is not None
        assert fetched.id == t.id
        assert fetched.config == {"event_type": "test"}

    def test_get_nonexistent_returns_none(self):
        store = TriggerStore(":memory:")
        assert store.get("nope") is None

    def test_list_all(self):
        store = TriggerStore(":memory:")
        store.save(_make_trigger())
        store.save(_make_trigger())
        assert len(store.list_all()) == 2

    def test_delete(self):
        store = TriggerStore(":memory:")
        t = _make_trigger()
        store.save(t)
        store.delete(t.id)
        assert store.get(t.id) is None

    def test_update_last_triggered(self):
        store = TriggerStore(":memory:")
        t = _make_trigger()
        store.save(t)
        store.update_last_triggered(t.id)
        fetched = store.get(t.id)
        assert fetched is not None
        assert fetched.last_triggered is not None
        assert fetched.trigger_count == 1


@pytest.mark.unit
class TestHeartbeatTriggerDataclass:
    def test_new_generates_id(self):
        t = _make_trigger()
        assert len(t.id) > 0

    def test_to_dict_roundtrip(self):
        t = _make_trigger(config={"key": "val"}, items=[{"action": "log"}])
        d = t.to_dict()
        assert d["type"] == "event"
        assert d["config"] == {"key": "val"}
        restored = HeartbeatTrigger.from_dict(d)
        assert restored.id == t.id
        assert restored.type == TriggerType.EVENT


@pytest.mark.unit
class TestEvaluateEventTrigger:
    def test_matching_event(self):
        t = _make_trigger(config={"event_type": "deploy.started"})
        assert evaluate_event_trigger(t, "deploy.started", {}) is True

    def test_non_matching_event(self):
        t = _make_trigger(config={"event_type": "deploy.started"})
        assert evaluate_event_trigger(t, "deploy.finished", {}) is False

    def test_wildcard_event(self):
        t = _make_trigger(config={"event_type": "*"})
        assert evaluate_event_trigger(t, "anything.here", {}) is True

    def test_disabled_trigger(self):
        t = _make_trigger(config={"event_type": "*"}, enabled=False)
        assert evaluate_event_trigger(t, "anything", {}) is False

    def test_wrong_type_returns_false(self):
        t = _make_trigger(trigger_type=TriggerType.CRON)
        assert evaluate_event_trigger(t, "test", {}) is False


@pytest.mark.unit
class TestEvaluateConditionTrigger:
    def test_gte_met(self):
        t = _make_trigger(
            trigger_type=TriggerType.CONDITION,
            config={"metric": "cpu", "threshold": 80, "operator": ">="},
        )
        assert evaluate_condition_trigger(t, {"cpu": 90}) is True

    def test_gte_not_met(self):
        t = _make_trigger(
            trigger_type=TriggerType.CONDITION,
            config={"metric": "cpu", "threshold": 80, "operator": ">="},
        )
        assert evaluate_condition_trigger(t, {"cpu": 50}) is False

    def test_equality(self):
        t = _make_trigger(
            trigger_type=TriggerType.CONDITION,
            config={"metric": "status", "threshold": 1, "operator": "=="},
        )
        assert evaluate_condition_trigger(t, {"status": 1}) is True
        assert evaluate_condition_trigger(t, {"status": 0}) is False

    def test_missing_metric(self):
        t = _make_trigger(
            trigger_type=TriggerType.CONDITION,
            config={"metric": "cpu", "threshold": 80},
        )
        assert evaluate_condition_trigger(t, {"memory": 90}) is False

    def test_missing_config_fields(self):
        t = _make_trigger(trigger_type=TriggerType.CONDITION, config={})
        assert evaluate_condition_trigger(t, {"x": 1}) is False


@pytest.mark.unit
class TestEvaluateMessageTrigger:
    def test_matching_pattern(self):
        t = _make_trigger(
            trigger_type=TriggerType.MESSAGE,
            config={"pattern": r"hello\s+world"},
        )
        assert evaluate_message_trigger(t, "say hello world now") is True

    def test_non_matching(self):
        t = _make_trigger(
            trigger_type=TriggerType.MESSAGE,
            config={"pattern": "xyz123"},
        )
        assert evaluate_message_trigger(t, "no match here") is False

    def test_case_insensitive(self):
        t = _make_trigger(
            trigger_type=TriggerType.MESSAGE,
            config={"pattern": "HELLO"},
        )
        assert evaluate_message_trigger(t, "hello there") is True

    def test_empty_pattern(self):
        t = _make_trigger(
            trigger_type=TriggerType.MESSAGE,
            config={"pattern": ""},
        )
        assert evaluate_message_trigger(t, "anything") is False

    def test_invalid_regex(self):
        t = _make_trigger(
            trigger_type=TriggerType.MESSAGE,
            config={"pattern": "[invalid"},
        )
        assert evaluate_message_trigger(t, "test") is False
