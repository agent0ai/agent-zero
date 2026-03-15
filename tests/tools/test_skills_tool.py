"""Tests for python/tools/skills_tool.py — SkillsTool."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.data = {}
    return agent


@pytest.fixture
def tool(mock_agent):
    from python.tools.skills_tool import SkillsTool
    return SkillsTool(
        agent=mock_agent,
        name="skills",
        method="list",
        args={},
        message="",
        loop_data=None,
    )


class TestSkillsToolList:
    @pytest.mark.asyncio
    async def test_list_returns_no_skills_when_empty(self, tool):
        with patch("python.tools.skills_tool.skills_helper.list_skills", return_value=[]):
            resp = await tool.execute(method="list")
        assert "No skills found" in resp.message
        assert resp.break_loop is False

    @pytest.mark.asyncio
    async def test_list_returns_skills_when_present(self, tool):
        mock_skill = MagicMock()
        mock_skill.name = "test-skill"
        mock_skill.tags = ["tag1"]
        mock_skill.version = "1.0"
        mock_skill.description = "A test skill"
        with patch("python.tools.skills_tool.skills_helper.list_skills", return_value=[mock_skill]):
            resp = await tool.execute(method="list")
        assert "test-skill" in resp.message
        assert "Available skills" in resp.message


class TestSkillsToolLoad:
    @pytest.mark.asyncio
    async def test_load_requires_skill_name(self, tool):
        resp = await tool.execute(method="load", skill_name="")
        assert "skill_name" in resp.message or "required" in resp.message.lower()

    @pytest.mark.asyncio
    async def test_load_skill_not_found(self, tool):
        with patch("python.tools.skills_tool.skills_helper.find_skill", return_value=None):
            resp = await tool.execute(method="load", skill_name="nonexistent")
        assert "not found" in resp.message or "Error" in resp.message

    @pytest.mark.asyncio
    async def test_load_success(self, tool):
        mock_skill = MagicMock()
        mock_skill.name = "my-skill"
        with patch("python.tools.skills_tool.skills_helper.find_skill", return_value=mock_skill):
            resp = await tool.execute(method="load", skill_name="my-skill")
        assert "Loaded" in resp.message
        assert "my-skill" in resp.message


class TestSkillsToolInvalidMethod:
    @pytest.mark.asyncio
    async def test_invalid_method_returns_error(self, tool):
        resp = await tool.execute(method="invalid")
        assert "Error" in resp.message or "method" in resp.message.lower()
