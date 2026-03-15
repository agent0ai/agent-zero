"""
Unit tests for python/helpers/knowledge_import.py — knowledge file importing,
calculate_checksum, load_knowledge with change detection and metadata.
"""
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ─── calculate_checksum ──────────────────────────────────────────────────────

class TestCalculateChecksum:
    def test_same_content_same_checksum(self, tmp_path):
        from python.helpers.knowledge_import import calculate_checksum
        f = tmp_path / "a.txt"
        f.write_text("hello world")
        c1 = calculate_checksum(str(f))
        c2 = calculate_checksum(str(f))
        assert c1 == c2
        assert len(c1) == 32  # MD5 hex

    def test_different_content_different_checksum(self, tmp_path):
        from python.helpers.knowledge_import import calculate_checksum
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("hello")
        f2.write_text("world")
        assert calculate_checksum(str(f1)) != calculate_checksum(str(f2))

    def test_empty_file_has_checksum(self, tmp_path):
        from python.helpers.knowledge_import import calculate_checksum
        f = tmp_path / "empty.txt"
        f.write_text("")
        c = calculate_checksum(str(f))
        assert c == "d41d8cd98f00b204e9800998ecf8427e"

    def test_binary_content(self, tmp_path):
        from python.helpers.knowledge_import import calculate_checksum
        f = tmp_path / "bin.dat"
        f.write_bytes(b"\x00\x01\x02\xff")
        c = calculate_checksum(str(f))
        assert len(c) == 32
        assert all(h in "0123456789abcdef" for h in c)


# ─── load_knowledge ──────────────────────────────────────────────────────────

class TestLoadKnowledge:
    def test_empty_knowledge_dir_returns_index(self):
        from python.helpers.knowledge_import import load_knowledge
        with patch("python.helpers.knowledge_import.PrintStyle"):
            result = load_knowledge(None, "", {})
        assert result == {}

    def test_no_knowledge_dir_specified_returns_index(self):
        from python.helpers.knowledge_import import load_knowledge
        with patch("python.helpers.knowledge_import.PrintStyle"):
            result = load_knowledge(None, "", {"existing": "data"})
        assert result == {"existing": "data"}

    def test_creates_missing_directory(self, tmp_path):
        from python.helpers.knowledge_import import load_knowledge
        kn_dir = tmp_path / "knowledge"
        assert not kn_dir.exists()
        with patch("python.helpers.knowledge_import.PrintStyle"):
            result = load_knowledge(None, str(kn_dir), {})
        assert kn_dir.exists()
        assert os.access(kn_dir, os.R_OK)

    def test_skips_files_without_extension(self, tmp_path):
        from python.helpers.knowledge_import import load_knowledge
        kn_dir = tmp_path / "kn"
        kn_dir.mkdir()
        (kn_dir / "noext").write_text("content")
        with patch("python.helpers.knowledge_import.PrintStyle"):
            result = load_knowledge(None, str(kn_dir), {})
        assert result == {}

    def test_skips_unsupported_file_types(self, tmp_path):
        from python.helpers.knowledge_import import load_knowledge
        kn_dir = tmp_path / "kn"
        kn_dir.mkdir()
        (kn_dir / "script.py").write_text("print('hi')")
        (kn_dir / "data.xml").write_text("<x/>")
        with patch("python.helpers.knowledge_import.PrintStyle"):
            result = load_knowledge(None, str(kn_dir), {})
        assert len(result) == 0

    def test_loads_txt_file(self, tmp_path):
        from python.helpers.knowledge_import import load_knowledge
        kn_dir = tmp_path / "kn"
        kn_dir.mkdir()
        (kn_dir / "doc.txt").write_text("Hello world")
        with patch("python.helpers.knowledge_import.PrintStyle"):
            result = load_knowledge(None, str(kn_dir), {})
        assert len(result) == 1
        key = str(kn_dir / "doc.txt")
        assert key in result
        data = result[key]
        assert data["file"] == key
        assert data["checksum"]
        assert data["state"] == "changed"
        assert len(data["documents"]) >= 1
        assert "source_file" in data["documents"][0].metadata
        assert data["documents"][0].metadata["knowledge_source"] is True

    def test_loads_md_file(self, tmp_path):
        from python.helpers.knowledge_import import load_knowledge
        kn_dir = tmp_path / "kn"
        kn_dir.mkdir()
        (kn_dir / "readme.md").write_text("# Title\n\nContent here.")
        with patch("python.helpers.knowledge_import.PrintStyle"):
            result = load_knowledge(None, str(kn_dir), {})
        assert len(result) == 1
        key = str(kn_dir / "readme.md")
        assert key in result
        assert len(result[key]["documents"]) >= 1

    def test_loads_json_as_text(self, tmp_path):
        from python.helpers.knowledge_import import load_knowledge
        kn_dir = tmp_path / "kn"
        kn_dir.mkdir()
        (kn_dir / "data.json").write_text('{"key": "value"}')
        with patch("python.helpers.knowledge_import.PrintStyle"):
            result = load_knowledge(None, str(kn_dir), {})
        assert len(result) == 1
        key = str(kn_dir / "data.json")
        assert key in result
        assert result[key]["documents"][0].metadata["file_type"] == "json"

    def test_unchanged_file_marked_original(self, tmp_path):
        from python.helpers.knowledge_import import load_knowledge
        kn_dir = tmp_path / "kn"
        kn_dir.mkdir()
        (kn_dir / "doc.txt").write_text("Same content")
        with patch("python.helpers.knowledge_import.PrintStyle"):
            result1 = load_knowledge(None, str(kn_dir), {})
        key = str(kn_dir / "doc.txt")
        checksum = result1[key]["checksum"]
        index = {key: {"file": key, "checksum": checksum, "ids": [], "state": "changed", "documents": []}}
        with patch("python.helpers.knowledge_import.PrintStyle"):
            result2 = load_knowledge(None, str(kn_dir), index)
        assert result2[key]["state"] == "original"
        assert result2[key]["documents"] == []

    def test_changed_file_reloaded(self, tmp_path):
        from python.helpers.knowledge_import import load_knowledge
        kn_dir = tmp_path / "kn"
        kn_dir.mkdir()
        f = kn_dir / "doc.txt"
        f.write_text("Original")
        with patch("python.helpers.knowledge_import.PrintStyle"):
            result1 = load_knowledge(None, str(kn_dir), {})
        key = str(f)
        index = {key: result1[key].copy()}
        f.write_text("Modified content")
        with patch("python.helpers.knowledge_import.PrintStyle"):
            result2 = load_knowledge(None, str(kn_dir), index)
        assert result2[key]["state"] == "changed"
        assert "Modified" in result2[key]["documents"][0].page_content

    def test_metadata_passed_through(self, tmp_path):
        from python.helpers.knowledge_import import load_knowledge
        kn_dir = tmp_path / "kn"
        kn_dir.mkdir()
        (kn_dir / "doc.txt").write_text("Content")
        metadata = {"custom_key": "custom_value", "area": "main"}
        with patch("python.helpers.knowledge_import.PrintStyle"):
            result = load_knowledge(None, str(kn_dir), {}, metadata=metadata)
        key = str(kn_dir / "doc.txt")
        doc_meta = result[key]["documents"][0].metadata
        assert doc_meta["custom_key"] == "custom_value"
        assert doc_meta["area"] == "main"
        assert doc_meta["source_file"] == "doc.txt"

    def test_log_item_stream_called_when_provided(self, tmp_path):
        from python.helpers.knowledge_import import load_knowledge
        kn_dir = tmp_path / "kn"
        kn_dir.mkdir()
        (kn_dir / "doc.txt").write_text("Content")
        log_item = MagicMock()
        with patch("python.helpers.knowledge_import.PrintStyle"):
            load_knowledge(log_item, str(kn_dir), {})
        assert log_item.stream.called

    def test_skips_hidden_files(self, tmp_path):
        from python.helpers.knowledge_import import load_knowledge
        kn_dir = tmp_path / "kn"
        kn_dir.mkdir()
        (kn_dir / ".hidden.txt").write_text("secret")
        (kn_dir / "visible.txt").write_text("public")
        with patch("python.helpers.knowledge_import.PrintStyle"):
            result = load_knowledge(None, str(kn_dir), {})
        assert len(result) == 1
        assert "visible.txt" in str(list(result.keys())[0])

    def test_load_error_continues_to_next_file(self, tmp_path):
        from python.helpers.knowledge_import import load_knowledge
        kn_dir = tmp_path / "kn"
        kn_dir.mkdir()
        (kn_dir / "good.txt").write_text("ok")
        (kn_dir / "corrupt.pdf").write_bytes(b"not a valid pdf")
        with patch("python.helpers.knowledge_import.PrintStyle"):
            result = load_knowledge(None, str(kn_dir), {})
        assert str(kn_dir / "good.txt") in result
        assert len(result) >= 1

    def test_directory_not_readable_returns_index(self, tmp_path):
        from python.helpers.knowledge_import import load_knowledge
        kn_dir = tmp_path / "kn"
        kn_dir.mkdir()
        with patch("python.helpers.knowledge_import.PrintStyle"):
            with patch("python.helpers.knowledge_import.os.access", return_value=False):
                result = load_knowledge(None, str(kn_dir), {"k": "v"})
        assert result == {"k": "v"}

    def test_recursive_glob_respects_recursive_flag(self, tmp_path):
        from python.helpers.knowledge_import import load_knowledge
        kn_dir = tmp_path / "kn"
        kn_dir.mkdir()
        sub = kn_dir / "sub"
        sub.mkdir()
        (sub / "nested.txt").write_text("nested")
        with patch("python.helpers.knowledge_import.PrintStyle"):
            result = load_knowledge(None, str(kn_dir), {}, recursive=True)
        assert len(result) >= 1
