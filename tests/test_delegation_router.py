"""Tests for DelegationRouter pattern matching and should_delegate."""

import asyncio

import pytest

from python.helpers.agent_composer import AgentComposer
from python.helpers.delegation_router import _CATEGORY_PATTERNS, DelegationRouter


@pytest.mark.unit
class TestCategoryPatterns:
    def test_research_pattern(self):
        pat = _CATEGORY_PATTERNS["research_tasks"]
        assert pat.search("Please research this topic")
        assert pat.search("Investigate the issue")
        assert not pat.search("Please write code")

    def test_content_pattern(self):
        pat = _CATEGORY_PATTERNS["content_tasks"]
        assert pat.search("Write a blog post")
        assert pat.search("Draft an article")
        assert not pat.search("deploy the server")

    def test_security_pattern(self):
        pat = _CATEGORY_PATTERNS["security_tasks"]
        assert pat.search("Run a security audit")
        assert pat.search("Found a vulnerability in the system")

    def test_devops_pattern(self):
        pat = _CATEGORY_PATTERNS["devops_tasks"]
        assert pat.search("Deploy to production")
        assert pat.search("Set up the CI/CD pipeline")
        assert pat.search("Create a docker container")

    def test_development_pattern(self):
        pat = _CATEGORY_PATTERNS["development_tasks"]
        assert pat.search("Implement the feature")
        assert pat.search("Fix the bug in auth")
        assert pat.search("Write a unit test")

    def test_operations_pattern(self):
        pat = _CATEGORY_PATTERNS["operations_tasks"]
        assert pat.search("Schedule a cron job")
        assert pat.search("Automate the workflow")


@pytest.mark.unit
class TestDelegationRouter:
    def test_no_rules_returns_none(self):
        composer = AgentComposer()
        router = DelegationRouter(composer)
        result = asyncio.run(router.should_delegate("research this", "__no_profile__"))
        assert result is None

    def test_get_delegation_rules_missing(self):
        composer = AgentComposer()
        router = DelegationRouter(composer)
        assert router.get_delegation_rules("__missing__") == {}

    def test_should_delegate_with_matching_rule(self):
        composer = AgentComposer()
        # Manually inject a manifest with delegation rules
        composer._manifest_cache["test_profile"] = {
            "behavior": {
                "auto_delegate": {
                    "research_tasks": "research-agent",
                    "content_tasks": "writer-agent",
                }
            }
        }
        router = DelegationRouter(composer)
        result = asyncio.run(router.should_delegate("Please research the market trends", "test_profile"))
        assert result == "research-agent"

    def test_should_delegate_no_match(self):
        composer = AgentComposer()
        composer._manifest_cache["test_profile"] = {
            "behavior": {
                "auto_delegate": {
                    "research_tasks": "research-agent",
                }
            }
        }
        router = DelegationRouter(composer)
        result = asyncio.run(router.should_delegate("What is the weather today?", "test_profile"))
        assert result is None

    def test_should_delegate_avoids_self(self):
        composer = AgentComposer()
        composer._manifest_cache["self_profile"] = {
            "behavior": {
                "auto_delegate": {
                    "development_tasks": "self_profile",
                }
            }
        }
        router = DelegationRouter(composer)
        result = asyncio.run(router.should_delegate("Implement a new feature", "self_profile"))
        assert result is None
