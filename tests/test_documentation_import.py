"""Test documentation import"""

from pathlib import Path


def test_reference_docs_directory_exists():
    """Reference documentation directory should exist"""
    ref_dir = Path(".claude/docs/mahoosuc-reference")
    assert ref_dir.exists()
    assert ref_dir.is_dir()


def test_key_reference_docs_imported():
    """Key reference documents should be imported"""
    ref_dir = Path(".claude/docs/mahoosuc-reference")

    key_docs = ["AGENT_REGISTRY_GUIDE.md", "SLASH_COMMANDS_REFERENCE.md", "SKILLS_REFERENCE.md"]

    for doc in key_docs:
        doc_path = ref_dir / doc
        assert doc_path.exists(), f"Missing reference doc: {doc}"


def test_import_summary_exists():
    """Import summary should document the migration"""
    summary = Path(".claude/docs/IMPORT_SUMMARY.md")
    assert summary.exists()

    content = summary.read_text()
    assert "Mahoosuc OS" in content
    assert "2026-01-24" in content
    assert "commands" in content.lower()
    assert "agents" in content.lower()
    assert "skills" in content.lower()
