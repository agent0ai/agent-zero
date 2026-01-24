"""Test Mahoosuc OS reference mode functionality"""


class TestReferenceMode:
    """Test reference mode - reading and parsing Mahoosuc resources"""

    def test_list_command_categories(self):
        """Should list all command categories"""
        from python.helpers.mahoosuc_reference import list_command_categories

        categories = list_command_categories()

        # Should have ~95 categories
        assert len(categories) >= 90

        # Should include key categories
        assert "devops" in categories
        assert "finance" in categories
        assert "auth" in categories

    def test_get_command_spec(self):
        """Should retrieve command specification"""
        from python.helpers.mahoosuc_reference import get_command_spec

        # Get devops:deploy command
        spec = get_command_spec("devops", "deploy")

        assert spec is not None
        assert "name" in spec or "deploy" in spec.lower()
        assert isinstance(spec, str)
        assert len(spec) > 100  # Should have substantial content

    def test_search_commands(self):
        """Should search commands by keyword"""
        from python.helpers.mahoosuc_reference import search_commands

        results = search_commands("deployment")

        assert len(results) > 0
        # Should find devops/deploy.md
        assert any("deploy" in r["file"].lower() for r in results)

    def test_list_agents_by_category(self):
        """Should list agents by category"""
        from python.helpers.mahoosuc_reference import list_agents_by_category

        agents = list_agents_by_category()

        assert "agent-os" in agents
        assert "product-management" in agents

        # agent-os should have 11 agents
        assert len(agents["agent-os"]) >= 10

    def test_get_agent_prompt(self):
        """Should retrieve agent prompt/spec"""
        from python.helpers.mahoosuc_reference import get_agent_prompt

        prompt = get_agent_prompt("agent-os", "implementer")

        assert prompt is not None
        assert isinstance(prompt, str)
        assert len(prompt) > 500  # Should be substantial

    def test_list_skills(self):
        """Should list all available skills"""
        from python.helpers.mahoosuc_reference import list_skills

        skills = list_skills()

        assert len(skills) == 5
        assert "brand-voice" in skills
        assert "content-optimizer" in skills
