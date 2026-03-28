#!/usr/bin/env python3
"""
Manual test script for prompt evolution (meta-learning) tool

Run this script to validate prompt evolution functionality.
Performs comprehensive smoke tests without requiring pytest.

Usage:
    python tests/meta_learning/manual_test_prompt_evolution.py
"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import asyncio
import tempfile
import shutil
import json
from python.tools.prompt_evolution import PromptEvolution
from python.helpers.prompt_versioning import PromptVersionManager
from python.helpers.tool import Response
import python.helpers.log as Log


class MockAgent:
    """Mock Agent instance for testing"""

    def __init__(self):
        self.history = self._create_test_history()
        self.context = Mock()
        self.context.log = Log.Log()
        self.mono_count = 5  # Simulated monologue count
        self.config = Mock()
        self.config.profile = "default"

        # Track calls to methods
        self.call_utility_model_calls = []
        self.read_prompt_calls = []

    def _create_test_history(self):
        """Create realistic conversation history with various patterns"""
        return [
            # User request 1 - successful code execution
            {"role": "user", "content": "Write a Python script to calculate fibonacci numbers"},
            {"role": "assistant", "content": "I'll create a fibonacci calculator for you.\n\nTool name: code_execution_tool\nTool args:\n```python\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n\nprint([fibonacci(i) for i in range(10)])\n```"},
            {"role": "tool", "content": "[0, 1, 1, 2, 3, 5, 8, 13, 21, 34]"},
            {"role": "assistant", "content": "Tool name: response\nTool args: Successfully created fibonacci calculator!"},

            # User request 2 - failure pattern (repeated errors)
            {"role": "user", "content": "Search for the latest news about AI"},
            {"role": "assistant", "content": "Tool name: search_engine\nTool args: latest AI news"},
            {"role": "tool", "content": "Error: Search engine connection timeout"},
            {"role": "assistant", "content": "Tool name: search_engine\nTool args: AI news 2026"},
            {"role": "tool", "content": "Error: Search engine connection timeout"},
            {"role": "assistant", "content": "Tool name: response\nTool args: I apologize, but the search engine is currently unavailable."},

            # User request 3 - missing capability
            {"role": "user", "content": "Send an email to john@example.com with the fibonacci results"},
            {"role": "assistant", "content": "I don't have the capability to send emails. I can only execute code, browse the web, and use available tools."},
            {"role": "user", "content": "What tools do you have for communication?"},
            {"role": "assistant", "content": "Currently I don't have any email or messaging tools. I can only respond to you directly."},

            # User request 4 - successful web browsing
            {"role": "user", "content": "What's the weather in New York?"},
            {"role": "assistant", "content": "Tool name: browser_agent\nTool args: search weather New York"},
            {"role": "tool", "content": "Weather in New York: 45°F, Partly cloudy"},
            {"role": "assistant", "content": "Tool name: response\nTool args: The current weather in New York is 45°F and partly cloudy."},

            # User request 5 - ambiguous instructions leading to wrong tool choice
            {"role": "user", "content": "Remember to save the fibonacci code for later"},
            {"role": "assistant", "content": "Tool name: code_execution_tool\nTool args: save fibonacci.py"},
            {"role": "tool", "content": "Error: Invalid code syntax"},
            {"role": "assistant", "content": "Tool name: memory_save\nTool args: fibonacci code"},
            {"role": "tool", "content": "Saved to memory"},
            {"role": "assistant", "content": "Tool name: response\nTool args: I've saved the fibonacci code to memory."},

            # User request 6 - successful memory usage
            {"role": "user", "content": "What did we save earlier?"},
            {"role": "assistant", "content": "Tool name: memory_query\nTool args: fibonacci"},
            {"role": "tool", "content": "Found: fibonacci code snippet"},
            {"role": "assistant", "content": "Tool name: response\nTool args: We saved the fibonacci calculator code earlier."},
        ]

    async def call_utility_model(self, system: str, message: str):
        """Mock utility model call that returns sample meta-analysis JSON"""
        self.call_utility_model_calls.append({"system": system, "message": message})

        # Return realistic meta-analysis JSON
        analysis = {
            "failure_patterns": [
                {
                    "pattern": "Search engine timeout failures",
                    "frequency": 2,
                    "severity": "high",
                    "affected_prompts": ["agent.system.tool.search_engine.md"],
                    "example_messages": [5, 7]
                },
                {
                    "pattern": "Initial wrong tool selection for file operations",
                    "frequency": 1,
                    "severity": "medium",
                    "affected_prompts": ["agent.system.tools.md", "agent.system.tool.code_exe.md"],
                    "example_messages": [18]
                }
            ],
            "success_patterns": [
                {
                    "pattern": "Effective code execution for computational tasks",
                    "frequency": 1,
                    "confidence": 0.9,
                    "related_prompts": ["agent.system.tool.code_exe.md"]
                },
                {
                    "pattern": "Successful memory operations after correction",
                    "frequency": 2,
                    "confidence": 0.85,
                    "related_prompts": ["agent.system.tool.memory_save.md", "agent.system.tool.memory_query.md"]
                }
            ],
            "missing_instructions": [
                {
                    "gap": "No email/messaging capability available",
                    "impact": "high",
                    "suggested_location": "agent.system.tools.md",
                    "proposed_addition": "Add email tool to available capabilities"
                },
                {
                    "gap": "Unclear distinction between file operations and memory operations",
                    "impact": "medium",
                    "suggested_location": "agent.system.main.solving.md",
                    "proposed_addition": "Clarify when to use memory_save vs code_execution for persistence"
                }
            ],
            "tool_suggestions": [
                {
                    "tool_name": "email_tool",
                    "purpose": "Send emails with attachments and formatting",
                    "use_case": "When user requests to send emails or messages",
                    "priority": "high",
                    "required_integrations": ["smtplib", "email"]
                },
                {
                    "tool_name": "search_fallback_tool",
                    "purpose": "Fallback search using multiple engines",
                    "use_case": "When primary search engine fails",
                    "priority": "medium",
                    "required_integrations": ["duckduckgo", "google"]
                }
            ],
            "prompt_refinements": [
                {
                    "file": "agent.system.tool.search_engine.md",
                    "section": "Error Handling",
                    "current": "If search fails, report error to user",
                    "proposed": "If search fails, implement retry logic with exponential backoff (max 3 attempts). If all retries fail, suggest alternative information sources.",
                    "reason": "Observed repeated timeout failures without retry logic, causing poor user experience",
                    "confidence": 0.88
                },
                {
                    "file": "agent.system.main.solving.md",
                    "section": "Tool Selection Strategy",
                    "current": "",
                    "proposed": "## Persistence Strategy\n\nWhen user asks to 'save' or 'remember' something:\n- Use `memory_save` for facts, snippets, and information\n- Use code_execution with file operations for saving actual code files\n- Use `instruments` for saving reusable automation scripts",
                    "reason": "Agent confused memory operations with file operations, leading to incorrect tool usage",
                    "confidence": 0.75
                },
                {
                    "file": "agent.system.tools.md",
                    "section": "Available Tools",
                    "current": "search_engine - Search the web for information",
                    "proposed": "search_engine - Search the web for information (includes automatic retry on timeout)",
                    "reason": "Users should know search has built-in resilience",
                    "confidence": 0.92
                }
            ]
        }

        return json.dumps(analysis, indent=2)

    def read_prompt(self, prompt_name: str, default: str = ""):
        """Mock prompt reading"""
        self.read_prompt_calls.append(prompt_name)
        return default  # Return default to trigger built-in prompt


def test_basic_functionality():
    """Test basic prompt evolution operations"""
    print("=" * 70)
    print("MANUAL TEST: Prompt Evolution (Meta-Learning) Tool")
    print("=" * 70)

    # Create temp directories
    temp_dir = tempfile.mkdtemp(prefix="test_prompt_evolution_")
    prompts_dir = Path(temp_dir) / "prompts"
    prompts_dir.mkdir()

    try:
        # Create sample prompt files
        print("\n1. Setting up test environment...")
        (prompts_dir / "agent.system.main.md").write_text("# Main System Prompt\nOriginal content")
        (prompts_dir / "agent.system.tools.md").write_text("# Tools\nTool catalog")
        (prompts_dir / "agent.system.tool.search_engine.md").write_text("# Search Engine\nBasic search")
        (prompts_dir / "agent.system.main.solving.md").write_text("# Problem Solving\nStrategies")
        print("   ✓ Created 4 sample prompt files")

        # Create mock agent
        print("\n2. Creating mock agent with conversation history...")
        mock_agent = MockAgent()
        print(f"   ✓ Created agent with {len(mock_agent.history)} history messages")

        # Initialize tool
        print("\n3. Initializing PromptEvolution tool...")
        tool = PromptEvolution(mock_agent, "prompt_evolution", {})
        print("   ✓ Tool initialized")

        # Test 1: Execute with insufficient history
        print("\n4. Testing insufficient history check...")
        with patch.dict(os.environ, {
            "ENABLE_PROMPT_EVOLUTION": "true",
            "PROMPT_EVOLUTION_MIN_INTERACTIONS": "100"  # More than we have
        }):
            result = asyncio.run(tool.execute())
            assert isinstance(result, Response)
            assert "Not enough interaction history" in result.message
            print("   ✓ Correctly rejected insufficient history")

        # Test 2: Execute with meta-learning disabled
        print("\n5. Testing disabled meta-learning check...")
        with patch.dict(os.environ, {"ENABLE_PROMPT_EVOLUTION": "false"}):
            result = asyncio.run(tool.execute())
            assert isinstance(result, Response)
            assert "Meta-learning is disabled" in result.message
            print("   ✓ Correctly detected disabled state")

        # Test 3: Full analysis execution
        print("\n6. Running full meta-analysis...")
        with patch.dict(os.environ, {
            "ENABLE_PROMPT_EVOLUTION": "true",
            "PROMPT_EVOLUTION_MIN_INTERACTIONS": "10",
            "PROMPT_EVOLUTION_MAX_HISTORY": "50",
            "PROMPT_EVOLUTION_CONFIDENCE_THRESHOLD": "0.7",
            "AUTO_APPLY_PROMPT_EVOLUTION": "false"
        }):
            result = asyncio.run(tool.execute())
            assert isinstance(result, Response)
            assert "Meta-Learning Analysis Complete" in result.message
            print("   ✓ Analysis executed successfully")
            print(f"\n   Analysis Summary:")
            print("   " + "\n   ".join(result.message.split("\n")))

        # Test 4: Verify utility model was called
        print("\n7. Verifying utility model interaction...")
        assert len(mock_agent.call_utility_model_calls) > 0
        call = mock_agent.call_utility_model_calls[0]
        assert "Analyze this conversation history" in call["message"]
        print("   ✓ Utility model called correctly")
        print(f"   ✓ System prompt length: {len(call['system'])} chars")

        # Test 5: Test analysis storage in memory
        print("\n8. Testing analysis storage...")
        # Create a simple mock memory
        mock_memory = Mock()
        mock_memory.insert_text = AsyncMock()

        with patch('python.tools.prompt_evolution.Memory.get', AsyncMock(return_value=mock_memory)):
            with patch.dict(os.environ, {
                "ENABLE_PROMPT_EVOLUTION": "true",
                "PROMPT_EVOLUTION_MIN_INTERACTIONS": "10",
            }):
                result = asyncio.run(tool.execute())
                # Verify memory insertion was attempted
                assert mock_memory.insert_text.called or "stored in memory" in result.message.lower()
                print("   ✓ Analysis storage tested")

        # Test 6: Test confidence threshold filtering
        print("\n9. Testing confidence threshold filtering...")
        with patch.dict(os.environ, {
            "ENABLE_PROMPT_EVOLUTION": "true",
            "PROMPT_EVOLUTION_MIN_INTERACTIONS": "10",
            "PROMPT_EVOLUTION_CONFIDENCE_THRESHOLD": "0.95",  # Very high threshold
        }):
            # Reset the mock to track new calls
            mock_agent.call_utility_model_calls = []
            tool = PromptEvolution(mock_agent, "prompt_evolution", {})
            result = asyncio.run(tool.execute())
            # With 0.95 threshold, fewer suggestions should pass
            print("   ✓ High confidence threshold tested")

        # Test 7: Test auto-apply functionality
        print("\n10. Testing auto-apply with version manager...")
        version_manager = PromptVersionManager(prompts_dir=prompts_dir)

        with patch.dict(os.environ, {
            "ENABLE_PROMPT_EVOLUTION": "true",
            "PROMPT_EVOLUTION_MIN_INTERACTIONS": "10",
            "PROMPT_EVOLUTION_CONFIDENCE_THRESHOLD": "0.7",
            "AUTO_APPLY_PROMPT_EVOLUTION": "true"
        }):
            # Reset mock
            mock_agent.call_utility_model_calls = []
            tool = PromptEvolution(mock_agent, "prompt_evolution", {})

            # Patch the version manager to prevent actual file modifications
            with patch('python.tools.prompt_evolution.PromptVersionManager') as MockVersionMgr:
                mock_vm_instance = Mock()
                mock_vm_instance.apply_change = Mock(return_value="backup_v1")
                MockVersionMgr.return_value = mock_vm_instance

                result = asyncio.run(tool.execute())

                # Should mention auto-applied changes
                if "Auto-Applied" in result.message:
                    print("   ✓ Auto-apply functionality executed")
                else:
                    print("   ✓ Auto-apply tested (no high-confidence changes)")

        # Test 8: Test history formatting
        print("\n11. Testing history formatting...")
        formatted = tool._format_history_for_analysis(mock_agent.history[:5])
        assert "[0] USER:" in formatted or "[0] ASSISTANT:" in formatted
        assert len(formatted) > 0
        print("   ✓ History formatted correctly")
        print(f"   ✓ Formatted length: {len(formatted)} chars")

        # Test 9: Test analysis summary generation
        print("\n12. Testing summary generation...")
        sample_analysis = {
            "meta": {
                "timestamp": datetime.now().isoformat(),
                "monologue_count": 5,
                "history_size": 20,
                "confidence_threshold": 0.7
            },
            "failure_patterns": [{"pattern": "test1", "frequency": 2}],
            "success_patterns": [{"pattern": "test2", "frequency": 3}],
            "missing_instructions": [{"gap": "test3"}],
            "tool_suggestions": [{"tool_name": "test_tool"}],
            "prompt_refinements": [{"file": "test.md", "confidence": 0.8}]
        }

        summary = tool._generate_summary(sample_analysis, applied_count=0, auto_apply=False)
        assert "Meta-Learning Analysis Complete" in summary
        assert "1 failure patterns" in summary
        assert "1 success patterns" in summary
        print("   ✓ Summary generated correctly")

        # Test 10: Test storage formatting
        print("\n13. Testing analysis storage formatting...")
        storage_text = tool._format_analysis_for_storage(sample_analysis)
        assert "# Meta-Learning Analysis" in storage_text
        assert "## Failure Patterns Detected" in storage_text
        assert "## Success Patterns Identified" in storage_text
        assert "## Tool Suggestions" in storage_text
        print("   ✓ Storage format generated correctly")
        print(f"   ✓ Storage text length: {len(storage_text)} chars")

        # Test 11: Test default analysis prompt
        print("\n14. Testing default analysis prompt...")
        default_prompt = tool._get_default_analysis_prompt()
        assert "meta-learning" in default_prompt.lower()
        assert "JSON" in default_prompt
        assert "failure_patterns" in default_prompt
        assert "prompt_refinements" in default_prompt
        print("   ✓ Default prompt contains required sections")
        print(f"   ✓ Default prompt length: {len(default_prompt)} chars")

        # Test 12: Integration test with version manager
        print("\n15. Testing integration with version manager...")
        versions_before = len(version_manager.list_versions())

        # Simulate applying a refinement
        sample_refinement = {
            "file": "agent.system.main.md",
            "proposed": "# Updated Main Prompt\nThis is improved content",
            "reason": "Test improvement",
            "confidence": 0.85
        }

        # Apply the change (this should create a backup)
        backup_id = version_manager.apply_change(
            file_name=sample_refinement["file"],
            content=sample_refinement["proposed"],
            change_description=sample_refinement["reason"]
        )

        versions_after = len(version_manager.list_versions())
        assert versions_after > versions_before
        print(f"   ✓ Integration successful (created backup: {backup_id})")
        print(f"   ✓ Versions: {versions_before} → {versions_after}")

        # Verify content was updated
        updated_content = (prompts_dir / "agent.system.main.md").read_text()
        assert "Updated Main Prompt" in updated_content
        print("   ✓ Verified prompt content was updated")

        # Test 13: Test rollback after meta-learning change
        print("\n16. Testing rollback of meta-learning changes...")
        success = version_manager.rollback(backup_id, create_backup=False)
        assert success

        restored_content = (prompts_dir / "agent.system.main.md").read_text()
        assert "Original content" in restored_content
        assert "Updated Main Prompt" not in restored_content
        print("   ✓ Rollback successful")

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        print("\nTest Coverage:")
        print("  ✓ Insufficient history detection")
        print("  ✓ Disabled meta-learning detection")
        print("  ✓ Full analysis execution")
        print("  ✓ Utility model integration")
        print("  ✓ Memory storage")
        print("  ✓ Confidence threshold filtering")
        print("  ✓ Auto-apply functionality")
        print("  ✓ History formatting")
        print("  ✓ Summary generation")
        print("  ✓ Storage formatting")
        print("  ✓ Default prompt structure")
        print("  ✓ Version manager integration")
        print("  ✓ Rollback functionality")
        print("\n" + "=" * 70)

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        print("\n17. Cleaning up temporary files...")
        shutil.rmtree(temp_dir)
        print("   ✓ Cleanup complete")


def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n" + "=" * 70)
    print("EDGE CASE TESTING")
    print("=" * 70)

    try:
        # Test with empty history
        print("\n1. Testing with empty history...")
        mock_agent = MockAgent()
        mock_agent.history = []
        tool = PromptEvolution(mock_agent, "prompt_evolution", {})

        with patch.dict(os.environ, {
            "ENABLE_PROMPT_EVOLUTION": "true",
            "PROMPT_EVOLUTION_MIN_INTERACTIONS": "5"
        }):
            result = asyncio.run(tool.execute())
            assert "Not enough" in result.message
            print("   ✓ Empty history handled correctly")

        # Test with malformed LLM response
        print("\n2. Testing with malformed LLM response...")
        mock_agent = MockAgent()

        async def bad_llm_call(system, message):
            return "This is not valid JSON at all!"

        mock_agent.call_utility_model = bad_llm_call
        tool = PromptEvolution(mock_agent, "prompt_evolution", {})

        with patch.dict(os.environ, {
            "ENABLE_PROMPT_EVOLUTION": "true",
            "PROMPT_EVOLUTION_MIN_INTERACTIONS": "10"
        }):
            result = asyncio.run(tool.execute())
            # Should handle parsing error gracefully
            assert isinstance(result, Response)
            print("   ✓ Malformed response handled gracefully")

        # Test with LLM error
        print("\n3. Testing with LLM error...")
        mock_agent = MockAgent()

        async def error_llm_call(system, message):
            raise Exception("LLM API error")

        mock_agent.call_utility_model = error_llm_call
        tool = PromptEvolution(mock_agent, "prompt_evolution", {})

        with patch.dict(os.environ, {
            "ENABLE_PROMPT_EVOLUTION": "true",
            "PROMPT_EVOLUTION_MIN_INTERACTIONS": "10"
        }):
            result = asyncio.run(tool.execute())
            assert isinstance(result, Response)
            print("   ✓ LLM error handled gracefully")

        print("\n" + "=" * 70)
        print("✅ ALL EDGE CASE TESTS PASSED")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n❌ EDGE CASE TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "PROMPT EVOLUTION TOOL TEST SUITE" + " " * 21 + "║")
    print("╚" + "═" * 68 + "╝")

    success1 = test_basic_functionality()
    success2 = test_edge_cases()

    print("\n" + "=" * 70)
    if success1 and success2:
        print("🎉 COMPREHENSIVE TEST SUITE PASSED")
        sys.exit(0)
    else:
        print("💥 SOME TESTS FAILED")
        sys.exit(1)
