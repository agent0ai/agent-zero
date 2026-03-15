"""Tests for python/helpers/browser_use_monkeypatch.py."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def mock_browser_use_llm():
    """Mock browser_use.llm so module can be imported without browser_use installed."""
    mock_llm = MagicMock()
    mock_llm.ChatGoogle = MagicMock()
    with patch.dict("sys.modules", {"browser_use": MagicMock(), "browser_use.llm": mock_llm}):
        if "python.helpers.browser_use_monkeypatch" in sys.modules:
            del sys.modules["python.helpers.browser_use_monkeypatch"]
        yield


class TestGeminiCleanAndConform:
    """Tests for gemini_clean_and_conform."""

    def test_returns_none_for_invalid_json(self):
        """Returns None when dirty_json.parse fails."""
        with patch("python.helpers.browser_use_monkeypatch.dirty_json") as mock_dj:
            mock_dj.parse.side_effect = ValueError("bad json")
            from python.helpers.browser_use_monkeypatch import gemini_clean_and_conform

            assert gemini_clean_and_conform("not valid") is None

    def test_returns_none_for_non_dict(self):
        """Returns None when parsed result is not a dict."""
        with patch("python.helpers.browser_use_monkeypatch.dirty_json") as mock_dj:
            mock_dj.parse.return_value = ["list"]
            from python.helpers.browser_use_monkeypatch import gemini_clean_and_conform

            assert gemini_clean_and_conform("[]") is None

    def test_complete_task_aliased_to_done(self):
        """complete_task action is normalized to done."""
        with patch("python.helpers.browser_use_monkeypatch.dirty_json") as mock_dj:
            mock_dj.parse.return_value = {"action": [{"complete_task": {"x": 1}}]}
            mock_dj.stringify.side_effect = lambda x: str(x)
            from python.helpers.browser_use_monkeypatch import gemini_clean_and_conform

            result = gemini_clean_and_conform("{}")
            assert result is not None
            actions = mock_dj.stringify.call_args[0][0]["action"]
            assert actions == [{"done": {"x": 1, "data": {"title": "Task Completed", "response": "Task completed successfully.", "page_summary": "No page summary available."}, "success": True}}]

    def test_scroll_down_normalized(self):
        """scroll_down action gets down=True and num_pages=1.0."""
        with patch("python.helpers.browser_use_monkeypatch.dirty_json") as mock_dj:
            mock_dj.parse.return_value = {"action": [{"scroll_down": {}}]}
            mock_dj.stringify.side_effect = lambda x: str(x)
            from python.helpers.browser_use_monkeypatch import gemini_clean_and_conform

            gemini_clean_and_conform("{}")
            actions = mock_dj.stringify.call_args[0][0]["action"]
            assert actions == [{"scroll": {"down": True, "num_pages": 1.0}}]

    def test_scroll_up_normalized(self):
        """scroll_up action gets down=False and num_pages=1.0."""
        with patch("python.helpers.browser_use_monkeypatch.dirty_json") as mock_dj:
            mock_dj.parse.return_value = {"action": [{"scroll_up": {}}]}
            mock_dj.stringify.side_effect = lambda x: str(x)
            from python.helpers.browser_use_monkeypatch import gemini_clean_and_conform

            gemini_clean_and_conform("{}")
            actions = mock_dj.stringify.call_args[0][0]["action"]
            assert actions == [{"scroll": {"down": False, "num_pages": 1.0}}]

    def test_go_to_url_gets_new_tab_default(self):
        """go_to_url action gets new_tab=False default."""
        with patch("python.helpers.browser_use_monkeypatch.dirty_json") as mock_dj:
            mock_dj.parse.return_value = {"action": [{"go_to_url": {"url": "https://x.com"}}]}
            mock_dj.stringify.side_effect = lambda x: str(x)
            from python.helpers.browser_use_monkeypatch import gemini_clean_and_conform

            gemini_clean_and_conform("{}")
            actions = mock_dj.stringify.call_args[0][0]["action"]
            assert actions == [{"go_to_url": {"url": "https://x.com", "new_tab": False}}]

    def test_done_constructs_data_from_response_summary_title(self):
        """done action constructs data from response, page_summary, title when missing."""
        with patch("python.helpers.browser_use_monkeypatch.dirty_json") as mock_dj:
            mock_dj.parse.return_value = {
                "action": [
                    {
                        "done": {
                            "response": "my response",
                            "page_summary": "my summary",
                            "title": "My Title",
                        }
                    }
                ]
            }
            mock_dj.stringify.side_effect = lambda x: str(x)
            from python.helpers.browser_use_monkeypatch import gemini_clean_and_conform

            gemini_clean_and_conform("{}")
            actions = mock_dj.stringify.call_args[0][0]["action"]
            d = actions[0]["done"]
            assert d["data"]["title"] == "My Title"
            assert d["data"]["response"] == "my response"
            assert d["data"]["page_summary"] == "my summary"
            assert d["success"] is True

    def test_skips_non_dict_action_items(self):
        """Non-dict items in action list are skipped."""
        with patch("python.helpers.browser_use_monkeypatch.dirty_json") as mock_dj:
            mock_dj.parse.return_value = {"action": ["string", 123, {"done": {"data": {}}}]}
            mock_dj.stringify.side_effect = lambda x: str(x)
            from python.helpers.browser_use_monkeypatch import gemini_clean_and_conform

            gemini_clean_and_conform("{}")
            actions = mock_dj.stringify.call_args[0][0]["action"]
            assert len(actions) == 1
            assert "done" in actions[0]


class TestPatchedFixGeminiSchema:
    """Tests for _patched_fix_gemini_schema monkey-patch."""

    def test_removes_title_from_required(self):
        """title is removed from required list."""
        from python.helpers.browser_use_monkeypatch import _patched_fix_gemini_schema

        schema = {"properties": {"a": {"type": "string"}}, "required": ["a", "title"]}
        result = _patched_fix_gemini_schema(MagicMock(), schema)
        assert "required" in result
        assert "title" not in result["required"]
        assert "a" in result["required"]

    def test_resolves_refs_from_defs(self):
        """$ref references are resolved from $defs."""
        from python.helpers.browser_use_monkeypatch import _patched_fix_gemini_schema

        schema = {
            "$defs": {"Foo": {"type": "string"}},
            "properties": {"x": {"$ref": "#/$defs/Foo"}},
        }
        result = _patched_fix_gemini_schema(MagicMock(), schema)
        assert "$defs" not in result
        assert result["properties"]["x"] == {"type": "string"}

    def test_removes_additionalProperties_title_default(self):
        """Unsupported keys additionalProperties, title, default are removed."""
        from python.helpers.browser_use_monkeypatch import _patched_fix_gemini_schema

        schema = {
            "properties": {"p": {"type": "string", "title": "P", "default": "x", "additionalProperties": True}},
        }
        result = _patched_fix_gemini_schema(MagicMock(), schema)
        p = result["properties"]["p"]
        assert "title" not in p
        assert "default" not in p
        assert "additionalProperties" not in p
        assert p["type"] == "string"

    def test_empty_object_gets_placeholder_property(self):
        """Empty object type gets _placeholder property for Gemini compatibility."""
        from python.helpers.browser_use_monkeypatch import _patched_fix_gemini_schema

        schema = {"type": "OBJECT", "properties": {}}
        result = _patched_fix_gemini_schema(MagicMock(), schema)
        assert result["properties"]["_placeholder"] == {"type": "string"}


class TestApply:
    """Tests for apply()."""

    def test_apply_patches_chat_google(self):
        """apply() sets ChatGoogle._fix_gemini_schema to patched version."""
        with patch("python.helpers.browser_use_monkeypatch.ChatGoogle") as mock_cg:
            from python.helpers.browser_use_monkeypatch import apply, _patched_fix_gemini_schema

            apply()
            assert mock_cg._fix_gemini_schema is _patched_fix_gemini_schema
