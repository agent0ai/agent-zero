"""Test custom skills import"""

from pathlib import Path


def test_skills_directory_not_empty():
    """Skills directory should contain imported skills"""
    skills_dir = Path(".claude/skills")
    items = list(skills_dir.iterdir())
    assert len(items) > 0, "Skills directory is empty"


def test_expected_skills_exist():
    """Expected skills should be imported"""
    skills_dir = Path(".claude/skills")
    expected = [
        "brand-voice",
        "content-optimizer",
        "frontend-design",
        "stripe-revenue-analyzer",
        "vercel-landing-page-builder",
    ]

    for skill in expected:
        skill_dir = skills_dir / skill
        assert skill_dir.exists(), f"Missing skill: {skill}"
        assert skill_dir.is_dir(), f"Skill not a directory: {skill}"


def test_skills_have_markdown_files():
    """Each skill should have at least one .md file"""
    skills_dir = Path(".claude/skills")

    for skill_dir in skills_dir.iterdir():
        if skill_dir.is_dir():
            md_files = list(skill_dir.glob("*.md"))
            assert len(md_files) > 0, f"Skill {skill_dir.name} has no .md files"


def test_skills_adaptation_doc_exists():
    """Skills adaptation documentation should exist"""
    doc = Path(".claude/docs/SKILLS_ADAPTATION.md")
    assert doc.exists()
    assert doc.stat().st_size > 0
