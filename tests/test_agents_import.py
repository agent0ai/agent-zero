"""Test custom agents import"""

from pathlib import Path

import yaml


def test_agents_directory_not_empty():
    """Agents directory should contain imported agents"""
    agents_dir = Path(".claude/agents")
    items = list(agents_dir.iterdir())
    assert len(items) > 0, "Agents directory is empty"


def test_agent_registry_exists():
    """Agent registry YAML should exist"""
    registry = Path(".claude/agents/registry.yaml")
    assert registry.exists()

    with open(registry) as f:
        data = yaml.safe_load(f)

    assert "metadata" in data
    assert "total_agents" in data["metadata"]


def test_agent_os_agents_exist():
    """Agent-os agents should be imported"""
    agent_os_dir = Path(".claude/agents/agent-os")
    assert agent_os_dir.exists()
    assert agent_os_dir.is_dir()

    # Should have multiple agent files
    agents = list(agent_os_dir.glob("*.md"))
    assert len(agents) > 5, f"Expected >5 agent-os agents, found {len(agents)}"


def test_product_management_agents_exist():
    """Product management agents should be imported"""
    pm_dir = Path(".claude/agents/product-management")
    assert pm_dir.exists()
    assert pm_dir.is_dir()

    agents = list(pm_dir.rglob("*.md"))
    assert len(agents) > 5, f"Expected >5 PM agents, found {len(agents)}"


def test_agents_migration_doc_exists():
    """Agent migration documentation should exist"""
    doc = Path(".claude/docs/AGENTS_MIGRATION.md")
    assert doc.exists()
    assert doc.stat().st_size > 0
