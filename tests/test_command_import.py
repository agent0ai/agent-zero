"""Test command category import"""

from pathlib import Path


def test_commands_directory_not_empty():
    """Commands directory should contain imported categories"""
    commands_dir = Path(".claude/commands")
    items = list(commands_dir.iterdir())
    assert len(items) > 0, "Commands directory is empty"


def test_command_categories_count():
    """Should have approximately 95 command categories"""
    commands_dir = Path(".claude/commands")
    categories = [d for d in commands_dir.iterdir() if d.is_dir() or d.suffix == ".md"]
    assert len(categories) >= 90, f"Expected ~95 categories, found {len(categories)}"


def test_commands_index_exists():
    """Commands index documentation should exist"""
    index = Path(".claude/docs/COMMANDS_INDEX.md")
    assert index.exists()
    assert index.stat().st_size > 0


def test_sample_commands_exist():
    """Key command categories should be present"""
    commands_dir = Path(".claude/commands")
    key_categories = ["devops", "finance", "auth", "travel", "research"]

    for category in key_categories:
        # Could be directory or .md file
        dir_path = commands_dir / category
        md_path = commands_dir / f"{category}.md"
        assert dir_path.exists() or md_path.exists(), f"Missing category: {category}"
