"""Tests for AgentComposer: load, inherit, compose, validate, tool_allowed."""

import pytest

from python.helpers.agent_composer import AgentComposer, AgentProfileConfig, get_composer


@pytest.mark.unit
class TestAgentComposer:
    def test_load_manifest_missing_returns_empty(self):
        composer = AgentComposer()
        m = composer.load_manifest("__nonexistent_profile__")
        assert m == {}

    def test_resolve_inheritance_single(self):
        composer = AgentComposer()
        chain = composer.resolve_inheritance("__nonexistent__")
        assert chain == ["__nonexistent__"]

    def test_compose_empty_profiles(self):
        composer = AgentComposer()
        cfg = composer.compose([])
        assert isinstance(cfg, AgentProfileConfig)
        assert cfg.capabilities == set()

    def test_compose_merges_layers(self):
        composer = AgentComposer()
        cfg = composer._merge_layers(
            [
                {
                    "name": "base",
                    "capabilities": ["read", "write"],
                    "tools": {"include": ["*"]},
                    "behavior": {"max_iterations": 10},
                },
                {
                    "name": "override",
                    "capabilities": ["execute"],
                    "tools": {"exclude": ["dangerous_*"]},
                    "behavior": {"max_iterations": 20},
                },
            ]
        )
        assert cfg.name == "override"
        assert "read" in cfg.capabilities
        assert "execute" in cfg.capabilities
        assert "dangerous_*" in cfg.tools["exclude"]
        assert cfg.behavior["max_iterations"] == 20

    def test_validate_config_empty_warnings(self):
        composer = AgentComposer()
        cfg = AgentProfileConfig()
        warnings = composer.validate_config(cfg)
        assert any("No capabilities" in w for w in warnings)
        assert any("No memory areas" in w for w in warnings)
        assert any("max_iterations" in w for w in warnings)

    def test_validate_config_clean(self):
        composer = AgentComposer()
        cfg = AgentProfileConfig(
            capabilities={"read"},
            memory_areas=["main"],
            behavior={"max_iterations": 10},
        )
        warnings = composer.validate_config(cfg)
        assert len(warnings) == 0

    def test_validate_config_tool_conflict(self):
        composer = AgentComposer()
        cfg = AgentProfileConfig(
            capabilities={"read"},
            tools={"include": ["*"], "exclude": ["dangerous"]},
            memory_areas=["main"],
            behavior={"max_iterations": 5},
        )
        warnings = composer.validate_config(cfg)
        assert any("both included" in w for w in warnings)

    def test_tool_allowed_no_rules(self):
        composer = AgentComposer()
        cfg = AgentProfileConfig()
        assert composer.tool_allowed(cfg, "anything") is True

    def test_tool_allowed_include_list(self):
        composer = AgentComposer()
        cfg = AgentProfileConfig(tools={"include": ["read_*", "write_*"], "exclude": []})
        assert composer.tool_allowed(cfg, "read_file") is True
        assert composer.tool_allowed(cfg, "delete_file") is False

    def test_tool_allowed_exclude_list(self):
        composer = AgentComposer()
        cfg = AgentProfileConfig(tools={"include": [], "exclude": ["rm_*"]})
        assert composer.tool_allowed(cfg, "rm_file") is False
        assert composer.tool_allowed(cfg, "read_file") is True

    def test_clear_cache(self):
        composer = AgentComposer()
        composer.load_manifest("__test__")
        assert "__test__" in composer._manifest_cache
        composer.clear_cache()
        assert len(composer._manifest_cache) == 0

    def test_get_composer_singleton(self):
        c1 = get_composer()
        c2 = get_composer()
        assert c1 is c2
