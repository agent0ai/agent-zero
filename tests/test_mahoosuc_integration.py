"""Integration tests for Mahoosuc OS import"""

from pathlib import Path

import pytest
import yaml


class TestMahoosucImport:
    """Test complete Mahoosuc OS import integration"""

    def test_complete_directory_structure(self):
        """All expected directories should exist"""
        base = Path(".claude")
        required = [
            "commands",
            "agents",
            "skills",
            "hooks",
            "validation",
            "docs",
            "docs/mahoosuc-reference",
        ]

        for subdir in required:
            path = base / subdir
            assert path.exists(), f"Missing: {subdir}"
            assert path.is_dir(), f"Not a directory: {subdir}"

    def test_content_counts(self):
        """Verify expected content volumes"""
        # Commands: should have ~95 categories
        commands = Path(".claude/commands")
        categories = [d for d in commands.iterdir() if d.is_dir() or d.suffix == ".md"]
        assert len(categories) >= 90, f"Expected ~95 categories, found {len(categories)}"

        # Command files: should have ~414 files
        command_files = list(commands.rglob("*.md"))
        assert len(command_files) >= 400, f"Expected ~414 commands, found {len(command_files)}"

        # Agents: should have 21+ agent files
        agent_files = list(Path(".claude/agents").rglob("*.md"))
        assert len(agent_files) >= 20, f"Expected 21 agents, found {len(agent_files)}"

        # Skills: should have 5 skill directories
        skill_dirs = [d for d in Path(".claude/skills").iterdir() if d.is_dir()]
        assert len(skill_dirs) >= 5, f"Expected 5 skills, found {len(skill_dirs)}"

    def test_agent_registry_valid_yaml(self):
        """Agent registry should be valid YAML"""
        registry = Path(".claude/agents/registry.yaml")
        assert registry.exists()

        with open(registry) as f:
            data = yaml.safe_load(f)

        assert "metadata" in data
        assert "version" in data["metadata"]
        assert "total_agents" in data["metadata"]
        assert data["metadata"]["total_agents"] >= 20

    def test_documentation_complete(self):
        """All documentation should be present"""
        docs_dir = Path(".claude/docs")
        required_docs = [
            "COMMANDS_INDEX.md",
            "AGENTS_MIGRATION.md",
            "SKILLS_ADAPTATION.md",
            "HOOKS_REFERENCE.md",
            "IMPORT_SUMMARY.md",
        ]

        for doc in required_docs:
            doc_path = docs_dir / doc
            assert doc_path.exists(), f"Missing doc: {doc}"
            assert doc_path.stat().st_size > 100, f"Doc too small: {doc}"

    def test_mahoosuc_reference_docs(self):
        """Reference documentation should be imported"""
        ref_dir = Path(".claude/docs/mahoosuc-reference")
        assert ref_dir.exists()

        # Should have multiple reference files
        ref_files = list(ref_dir.glob("*.md"))
        assert len(ref_files) >= 10, f"Expected 10+ reference docs, found {len(ref_files)}"

    def test_no_broken_structure(self):
        """No empty required directories"""
        base = Path(".claude")

        # These directories must have content
        must_have_content = ["commands", "agents", "skills", "docs"]

        for subdir in must_have_content:
            path = base / subdir
            items = list(path.iterdir())
            assert len(items) > 0, f"Empty directory: {subdir}"


class TestCommandCategories:
    """Test specific command categories"""

    @pytest.mark.parametrize("category", ["devops", "finance", "auth", "travel", "research"])
    def test_key_categories_exist(self, category):
        """Key command categories should exist"""
        commands_dir = Path(".claude/commands")
        cat_dir = commands_dir / category
        cat_file = commands_dir / f"{category}.md"

        assert cat_dir.exists() or cat_file.exists(), f"Missing category: {category}"

    def test_devops_commands_exist(self):
        """DevOps category should have multiple commands"""
        devops = Path(".claude/commands/devops")
        if devops.exists() and devops.is_dir():
            commands = list(devops.glob("*.md"))
            assert len(commands) > 0, "DevOps category has no commands"


class TestAgentCategories:
    """Test agent organization"""

    def test_agent_os_category(self):
        """Agent-OS category should exist with agents"""
        agent_os = Path(".claude/agents/agent-os")
        assert agent_os.exists()
        assert agent_os.is_dir()

        agents = list(agent_os.glob("*.md"))
        assert len(agents) >= 10, f"Expected 10+ agent-os agents, found {len(agents)}"

    def test_product_management_category(self):
        """Product management category should exist"""
        pm = Path(".claude/agents/product-management")
        assert pm.exists()
        assert pm.is_dir()

        # PM agents may be in subdirectories
        agents = list(pm.rglob("*.md"))
        assert len(agents) >= 5, f"Expected 5+ PM agents, found {len(agents)}"


class TestSkills:
    """Test skill imports"""

    @pytest.mark.parametrize(
        "skill",
        [
            "brand-voice",
            "content-optimizer",
            "frontend-design",
            "stripe-revenue-analyzer",
            "vercel-landing-page-builder",
        ],
    )
    def test_skill_exists(self, skill):
        """Each expected skill should exist"""
        skill_dir = Path(".claude/skills") / skill
        assert skill_dir.exists(), f"Missing skill: {skill}"
        assert skill_dir.is_dir(), f"Skill not a directory: {skill}"

        # Should have at least one markdown file
        md_files = list(skill_dir.glob("*.md"))
        assert len(md_files) > 0, f"Skill {skill} has no .md files"
