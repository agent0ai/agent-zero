"""Test hooks and validation import"""

from pathlib import Path


def test_hooks_directory_not_empty():
    """Hooks directory should contain imported hooks"""
    hooks_dir = Path(".claude/hooks")
    items = list(hooks_dir.iterdir())
    assert len(items) > 0, "Hooks directory is empty"


def test_validation_directory_not_empty():
    """Validation directory should contain validation rules"""
    validation_dir = Path(".claude/validation")
    items = list(validation_dir.iterdir())
    assert len(items) > 0, "Validation directory is empty"


def test_hooks_reference_exists():
    """Hooks reference documentation should exist"""
    doc = Path(".claude/docs/HOOKS_REFERENCE.md")
    assert doc.exists()
    assert doc.stat().st_size > 0


def test_hooks_have_structure():
    """Hooks should have organized structure"""
    hooks_dir = Path(".claude/hooks")

    # Check for common hook types from Mahoosuc OS
    hook_types = ["on-error", "on-file-change", "periodic", "post-deploy", "pre-commit"]

    # At least some hook types should exist
    found = [ht for ht in hook_types if (hooks_dir / ht).exists()]
    assert len(found) > 0, "No standard hook directories found"
