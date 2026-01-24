"""Test .claude directory structure"""

import os
from pathlib import Path


def test_claude_directory_exists():
    """Claude directory should exist in project root"""
    claude_dir = Path(".claude")
    assert claude_dir.exists()
    assert claude_dir.is_dir()


def test_claude_subdirectories_exist():
    """Required subdirectories should exist"""
    base = Path(".claude")
    required = ["commands", "agents", "skills", "hooks", "validation", "docs"]

    for subdir in required:
        path = base / subdir
        assert path.exists(), f"Missing directory: {subdir}"
        assert path.is_dir(), f"Not a directory: {subdir}"


def test_claude_structure_readable():
    """All .claude directories should be readable"""
    base = Path(".claude")
    for item in base.rglob("*"):
        if item.is_dir():
            assert os.access(item, os.R_OK), f"Directory not readable: {item}"
