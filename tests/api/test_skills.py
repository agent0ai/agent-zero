"""Tests for python/api/skills.py — Skills API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.skills import Skills


def _make_handler(app=None, lock=None):
    return Skills(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestSkills:
    @pytest.mark.asyncio
    async def test_list_action_returns_ok_with_skills(self):
        handler = _make_handler()
        with patch.object(handler, "list_skills", return_value=[{"name": "skill1", "path": "/p/skill1"}]):
            result = await handler.process({"action": "list"}, MagicMock())
        assert result["ok"] is True
        assert len(result["data"]) == 1
        assert result["data"][0]["name"] == "skill1"

    @pytest.mark.asyncio
    async def test_delete_action_returns_ok(self):
        handler = _make_handler()
        with patch.object(handler, "delete_skill", return_value={"ok": True, "skill_path": "/p/skill"}):
            result = await handler.process({"action": "delete", "skill_path": "/p/skill"}, MagicMock())
        assert result["ok"] is True
        assert result["data"]["skill_path"] == "/p/skill"

    @pytest.mark.asyncio
    async def test_invalid_action_returns_error(self):
        handler = _make_handler()
        result = await handler.process({"action": "invalid"}, MagicMock())
        assert result["ok"] is False
        assert "Invalid action" in result["error"]

    @pytest.mark.asyncio
    async def test_delete_skill_raises_when_path_missing(self):
        handler = _make_handler()
        result = await handler.process({"action": "delete"}, MagicMock())
        assert result["ok"] is False
        assert "skill_path" in result["error"]


class TestSkillsListSkills:
    def test_list_skills_returns_from_helper(self):
        handler = _make_handler()
        mock_skills = [
            MagicMock(name="s1", description="d1", path=Path("/p/s1")),
            MagicMock(name="s2", description="d2", path=Path("/p/s2")),
        ]
        mock_skills[0].name = "s1"
        mock_skills[0].description = "d1"
        mock_skills[0].path = Path("/p/s1")
        mock_skills[1].name = "s2"
        mock_skills[1].description = "d2"
        mock_skills[1].path = Path("/p/s2")
        with patch("python.api.skills.skills.list_skills", return_value=mock_skills):
            result = handler.list_skills({})
        assert len(result) == 2
        assert result[0]["name"] == "s1"
        assert result[1]["name"] == "s2"

    def test_list_skills_filters_by_project(self):
        handler = _make_handler()
        skill = MagicMock()
        skill.name = "s1"
        skill.description = "d1"
        skill.path = Path("/proj/skills/s1")
        with patch("python.api.skills.skills.list_skills", return_value=[skill]), \
             patch("python.api.skills.projects.get_project_folder", return_value="/proj"), \
             patch("python.api.skills.runtime.is_development", return_value=False), \
             patch("python.api.skills.files.is_in_dir", return_value=True):
            result = handler.list_skills({"project_name": "myproj"})
        assert len(result) == 1


class TestSkillsDeleteSkill:
    def test_delete_skill_raises_when_path_empty(self):
        handler = _make_handler()
        with pytest.raises(Exception, match="skill_path is required"):
            handler.delete_skill({"skill_path": ""})

    def test_delete_skill_calls_helper(self):
        handler = _make_handler()
        with patch("python.api.skills.skills.delete_skill") as mock_delete:
            result = handler.delete_skill({"skill_path": "/path/to/skill"})
        mock_delete.assert_called_once_with("/path/to/skill")
        assert result["ok"] is True
        assert result["skill_path"] == "/path/to/skill"
