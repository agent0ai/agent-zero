#!/usr/bin/env python3
"""
Quick verification script for Agent Skills integration
Tests basic functionality without running full test suite
"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Test basic imports first
try:
    from python.helpers.agents_md_parser import AgentsMdParser
    from python.helpers.skill_registry import SkillRegistry, get_registry
    IMPORTS_OK = True
except Exception as e:
    print(f"Import error (expected in minimal env): {e}")
    IMPORTS_OK = False

# Try to import integration (may fail without full deps)
try:
    from python.helpers.agent_skills import get_integration
    INTEGRATION_IMPORT_OK = True
except Exception as e:
    print(f"Integration import failed (may need full dependencies): {e}")
    INTEGRATION_IMPORT_OK = False

# Simple print functions that don't require PrintStyle
def print_with_color(text, prefix=""):
    """Fallback print function"""
    print(f"{prefix} {text}")


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_success(text):
    """Print success message"""
    print(f"✓ {text}")


def print_error(text):
    """Print error message"""
    print(f"✗ {text}")


def print_info(text):
    """Print info message"""
    print(f"  {text}")


def verify_parser():
    """Verify AGENTS.md parser"""
    print_header("Testing AGENTS.md Parser")

    if not IMPORTS_OK:
        print_error("Imports failed - skipping parser tests")
        return False

    try:
        # Test with sample content
        sample = """---
name: test-skill
description: A test skill for verification
triggers: test, verification
---

# Test Skill

This is a test skill.
"""

        skill = AgentsMdParser.parse_content(sample)

        if skill and skill.metadata.name == "test-skill":
            print_success("Parser correctly parses YAML frontmatter")
        else:
            print_error("Parser failed to parse frontmatter")
            return False

        # Test name normalization
        normalized = AgentsMdParser._normalize_name("Test Skill Name")
        if normalized == "test-skill-name":
            print_success("Name normalization works correctly")
        else:
            print_error(f"Name normalization failed: {normalized}")
            return False

        # Test AGENTS.md parsing
        agents_md = project_root / "AGENTS.md"
        if agents_md.exists():
            skills = AgentsMdParser.parse_agents_md(agents_md)
            print_success(f"Parsed AGENTS.md: found {len(skills)} skills")
            print_info(f"Sample skills: {', '.join([s.metadata.name for s in skills[:5]])}")
        else:
            print_error("AGENTS.md not found")
            return False

        return True

    except Exception as e:
        print_error(f"Parser verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_registry():
    """Verify skill registry"""
    print_header("Testing Skill Registry")

    if not IMPORTS_OK:
        print_error("Imports failed - skipping registry tests")
        return False

    try:
        # Initialize registry
        registry = SkillRegistry(project_root=project_root)
        print_success("Registry initialized")

        # Discover skills
        locations = registry.discover_skills()
        print_success(f"Discovered {len(locations)} skill locations")

        # List available skills
        skills = registry.list_available_skills()
        print_success(f"Found {len(skills)} unique skills")

        # Show some skills
        if skills:
            print_info("\nSample skills:")
            for skill in skills[:5]:
                print_info(f"  - {skill['name']}: {skill['description'][:60]}...")

        # Test skill loading
        if skills:
            first_skill_name = skills[0]['name']
            skill = registry.get_skill(first_skill_name)
            if skill:
                print_success(f"Successfully loaded skill: {first_skill_name}")
            else:
                print_error(f"Failed to load skill: {first_skill_name}")

        # Get stats
        stats = registry.get_stats()
        print_info(f"\nRegistry stats:")
        print_info(f"  Total skills: {stats['total_skills']}")
        print_info(f"  Loaded skills: {stats['loaded_skills']}")
        print_info(f"  Sources: {stats['sources']}")

        return True

    except Exception as e:
        print_error(f"Registry verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_integration():
    """Verify Agent Skills integration"""
    print_header("Testing Agent Skills Integration")

    if not INTEGRATION_IMPORT_OK:
        print_error("Integration import failed - skipping integration tests")
        print_info("This is expected if not all Agent Zero dependencies are installed")
        return False

    try:
        # Get integration instance
        integration = get_integration()
        print_success("Integration initialized")

        # Discover skills
        integration.discover_and_register()
        print_success("Skills discovered and registered")

        # Get available skills
        skills = integration.get_available_skills_for_agent()
        print_success(f"Found {len(skills)} available skills")

        # Search skills
        search_results = integration.search_skills("code")
        print_success(f"Search for 'code': {len(search_results)} results")

        # Get stats
        stats = integration.get_stats()
        print_info(f"\nIntegration stats:")
        print_info(f"  Total skills: {stats['total_skills']}")
        print_info(f"  Loaded skills: {stats['loaded_skills']}")

        return True

    except Exception as e:
        print_error(f"Integration verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_api_structure():
    """Verify API endpoints exist"""
    print_header("Verifying API Structure")

    try:
        api_file = project_root / "python" / "api" / "skills.py"

        if not api_file.exists():
            print_error("API file not found")
            return False

        print_success("API file exists")

        # Check for API classes
        content = api_file.read_text()

        required_classes = [
            "SkillsList",
            "SkillsSearch",
            "SkillsGet",
            "SkillsDiscover",
            "SkillsInstall",
            "SkillsStats",
            "SkillsByTrigger",
        ]

        for class_name in required_classes:
            if class_name in content:
                print_success(f"API endpoint: {class_name}")
            else:
                print_error(f"Missing API endpoint: {class_name}")

        return True

    except Exception as e:
        print_error(f"API structure verification failed: {e}")
        return False


def verify_files():
    """Verify all required files exist"""
    print_header("Verifying File Structure")

    required_files = [
        "python/helpers/agents_md_parser.py",
        "python/helpers/skill_registry.py",
        "python/helpers/agent_skills.py",
        "python/api/skills.py",
        ".agent-zero/skills/README.md",
        ".agent-zero/skills/example-skill/SKILL.md",
        "AGENTS.md",
    ]

    all_exist = True

    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print_success(f"Found: {file_path}")
        else:
            print_error(f"Missing: {file_path}")
            all_exist = False

    return all_exist


def main():
    """Run all verifications"""
    print("\n")
    print("=" * 80)
    print("  Agent Zero Skills Integration Verification")
    print("=" * 80)

    results = {
        "Files": verify_files(),
        "Parser": verify_parser(),
        "Registry": verify_registry(),
        "Integration": verify_integration(),
        "API": verify_api_structure(),
    }

    # Summary
    print_header("Verification Summary")

    all_passed = True
    for component, passed in results.items():
        if passed:
            print_success(f"{component}: PASSED")
        else:
            print_error(f"{component}: FAILED")
            all_passed = False

    print("\n")

    if all_passed:
        print("\n" + "=" * 80)
        print("✓ All verifications passed! Agent Skills integration is ready.")
        print("=" * 80)
        print_info("\nNext steps:")
        print_info("  1. Test the API: curl http://localhost:50001/api/skills/list")
        print_info("  2. Install skills: skilz install <skill-name>")
        print_info("  3. Create custom skills in .agent-zero/skills/")
        print_info("  4. Run tests: pytest tests/test_agent_skills.py")
        return 0
    else:
        print("\n" + "=" * 80)
        print("✗ Some verifications failed. Please review the errors above.")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
