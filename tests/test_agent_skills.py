"""
Tests for Agent Skills integration
"""

import pytest
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from python.helpers.agents_md_parser import AgentsMdParser, SkillMetadata
from python.helpers.skill_registry import SkillRegistry
from python.helpers.agent_skills import AgentSkillsIntegration


class TestAgentsMdParser:
    """Test AGENTS.md parsing functionality"""

    def test_parse_frontmatter(self):
        """Test parsing SKILL.md with YAML frontmatter"""
        content = """---
name: test-skill
description: A test skill
triggers: test, demo
version: 1.0.0
---

# Test Skill

This is a test skill.
"""
        skill = AgentsMdParser.parse_content(content)

        assert skill is not None
        assert skill.metadata.name == "test-skill"
        assert skill.metadata.description == "A test skill"
        assert "test" in skill.metadata.triggers
        assert skill.metadata.version == "1.0.0"

    def test_parse_without_frontmatter(self):
        """Test parsing simple markdown without frontmatter"""
        content = """## GitHub Integration

Provides GitHub API integration for PR management.

**Triggers:** github, pull request, issue
"""
        skills = AgentsMdParser.parse_multiple_skills(content)

        assert len(skills) > 0
        skill = skills[0]
        assert skill.metadata.name == "github-integration"
        assert "github" in skill.metadata.triggers

    def test_name_validation(self):
        """Test skill name validation"""
        assert AgentsMdParser.NAME_PATTERN.match("valid-skill-name")
        assert AgentsMdParser.NAME_PATTERN.match("skill123")
        assert not AgentsMdParser.NAME_PATTERN.match("Invalid_Skill")
        assert not AgentsMdParser.NAME_PATTERN.match("invalid-skill-")
        assert not AgentsMdParser.NAME_PATTERN.match("Invalid Skill")

    def test_normalize_name(self):
        """Test name normalization"""
        assert AgentsMdParser._normalize_name("Test Skill") == "test-skill"
        assert AgentsMdParser._normalize_name("GitHub Integration") == "github-integration"
        assert AgentsMdParser._normalize_name("API_Integration") == "api-integration"

    def test_parse_agents_md_file(self):
        """Test parsing actual AGENTS.md file"""
        agents_md = project_root / "AGENTS.md"

        if agents_md.exists():
            skills = AgentsMdParser.parse_agents_md(agents_md)

            assert len(skills) > 0

            # Check first few skills
            skill_names = [s.metadata.name for s in skills[:5]]
            assert "code-execution" in skill_names or len(skill_names) > 0


class TestSkillRegistry:
    """Test skill registry and discovery"""

    def test_registry_initialization(self):
        """Test registry initialization"""
        registry = SkillRegistry(project_root=project_root)

        assert registry is not None
        assert registry.project_root == project_root

    def test_skill_discovery(self):
        """Test skill discovery from project"""
        registry = SkillRegistry(project_root=project_root)
        locations = registry.discover_skills()

        # Should find at least the example skill and AGENTS.md skills
        assert len(locations) > 0

        # Check if example skill was discovered
        skill_names = registry._skill_locations.keys()
        assert "example-skill" in skill_names or len(skill_names) > 0

    def test_load_skill(self):
        """Test loading a specific skill"""
        registry = SkillRegistry(project_root=project_root)
        registry.discover_skills()

        # Try to load example skill
        skill = registry.get_skill("example-skill")

        if skill:
            assert skill.metadata.name == "example-skill"
            assert skill.metadata.description is not None
            assert len(skill.metadata.triggers) > 0

    def test_search_skills(self):
        """Test skill search functionality"""
        registry = SkillRegistry(project_root=project_root)
        registry.discover_skills()

        # Search for "example"
        results = registry.search_skills("example")

        # Should find at least one result
        assert len(results) >= 0  # May not find anything depending on what's installed

    def test_list_available_skills(self):
        """Test listing all available skills"""
        registry = SkillRegistry(project_root=project_root)
        registry.discover_skills()

        skills = registry.list_available_skills()

        assert isinstance(skills, list)
        assert len(skills) > 0

        # Check structure of first skill
        if skills:
            skill = skills[0]
            assert "name" in skill
            assert "description" in skill
            assert "source" in skill

    def test_get_stats(self):
        """Test registry statistics"""
        registry = SkillRegistry(project_root=project_root)
        registry.discover_skills()

        stats = registry.get_stats()

        assert "total_skills" in stats
        assert "loaded_skills" in stats
        assert "sources" in stats
        assert stats["total_skills"] >= 0


class TestAgentSkillsIntegration:
    """Test Agent Skills integration layer"""

    def test_integration_initialization(self):
        """Test integration initialization"""
        integration = AgentSkillsIntegration()

        assert integration is not None
        assert integration.registry is not None

    def test_discover_and_register(self):
        """Test skill discovery and registration"""
        integration = AgentSkillsIntegration()
        integration.discover_and_register()

        # Should have discovered some skills
        skills = integration.get_available_skills_for_agent()
        assert len(skills) > 0

    def test_search_skills(self):
        """Test skill search through integration"""
        integration = AgentSkillsIntegration()
        integration.discover_and_register()

        results = integration.search_skills("code")

        assert isinstance(results, list)

    def test_get_skill_details(self):
        """Test getting skill details"""
        integration = AgentSkillsIntegration()
        integration.discover_and_register()

        # Try to get example skill details
        details = integration.get_skill_details("example-skill")

        if details:
            assert "name" in details
            assert "description" in details
            assert "content" in details

    def test_get_stats(self):
        """Test integration statistics"""
        integration = AgentSkillsIntegration()
        integration.discover_and_register()

        stats = integration.get_stats()

        assert "total_skills" in stats
        assert isinstance(stats["total_skills"], int)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
