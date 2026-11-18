"""Exercise scanner budgets with real files and real cl100k_base token counts."""

from pathlib import Path

import pytest

from helpers import tokens
from plugins._promptinclude.helpers.scanner import scan_promptinclude_files


@pytest.mark.parametrize("file_cap", [2000, 30000], ids=["per-file", "remaining-total"])
def test_scanner_caps_mixed_density_content(tmp_path: Path, file_cap: int) -> None:
    path = tmp_path / "dense.promptinclude.md"
    raw = "😀" * 10000 + " " * 100000
    path.write_text(raw, encoding="utf-8")
    total_cap = 8000

    result = scan_promptinclude_files(
        str(tmp_path), max_file_tokens=file_cap, max_total_tokens=total_cap
    )

    assert result["skipped_count"] == 0
    (entry,) = result["files"]
    actual = tokens.count_tokens(entry["content"])
    assert entry["status"] == "cropped"
    assert entry["token_count"] == actual
    assert 0 < actual <= file_cap
    assert actual + tokens.count_tokens(entry["path"]) + 5 <= total_cap
    assert raw.startswith(entry["content"][:-3])
    assert entry["content"].endswith("...")
    assert "\ufffd" not in entry["content"]


def test_scanner_accounts_for_previous_files_and_path_overhead(tmp_path: Path) -> None:
    first = "ordinary instruction\n" * 20
    (tmp_path / "a.promptinclude.md").write_text(first, encoding="utf-8")
    (tmp_path / "b.promptinclude.md").write_text(
        "😀" * 1000 + " " * 10000, encoding="utf-8"
    )
    (tmp_path / "c.promptinclude.md").write_text("last instruction", encoding="utf-8")
    total_cap = 400

    result = scan_promptinclude_files(
        str(tmp_path), max_file_tokens=2000, max_total_tokens=total_cap
    )

    assert [entry["status"] for entry in result["files"]] == ["ok", "cropped"]
    assert result["files"][0]["content"] == first
    assert result["skipped_count"] == 1
    actual_total = 0
    for entry in result["files"]:
        actual = tokens.count_tokens(entry["content"])
        assert entry["token_count"] == actual
        actual_total += actual + tokens.count_tokens(entry["path"]) + 5
    assert actual_total <= total_cap


def test_scanner_preserves_ordinary_files_and_ignores(tmp_path: Path) -> None:
    content = "Keep replies concise."
    path = tmp_path / "rules.promptinclude.md"
    path.write_text(content, encoding="utf-8")
    (tmp_path / "empty.promptinclude.md").write_text(" \n", encoding="utf-8")
    (tmp_path / "ignored.promptinclude.md").write_text("not included", encoding="utf-8")

    result = scan_promptinclude_files(
        str(tmp_path), gitignore="ignored.promptinclude.md"
    )

    assert result == {
        "files": [
            {
                "path": str(path),
                "content": content,
                "token_count": tokens.count_tokens(content),
                "status": "ok",
            }
        ],
        "skipped_count": 0,
    }
