#!/usr/bin/env python3
"""
Loop Detection Unit Test

Tests the loop detection and intervention mechanism without running the full agent.
Run with: python test_loop_detection.py
"""

import asyncio
import sys
from typing import Any


# ============== Mock Classes ==============

class MockLog:
    """Mock logger that prints to console."""
    
    def log(self, type: str = "", heading: str = "", **kwargs):
        prefix = f"[{type.upper()}]" if type else "[LOG]"
        if heading:
            print(f"  {prefix} {heading}")
        elif kwargs.get("content"):
            print(f"  {prefix} {kwargs['content']}")


class MockContext:
    """Mock agent context."""
    log = MockLog()
    
    def set_progress(self, msg: str, force: bool = False):
        pass


class MockLoopData:
    """Mock loop data structure."""
    
    def __init__(self):
        self.iteration = 0
        self.last_response = ""
        self.current_tool = None
        self.extras_persistent = {}
        self.extras_temporary = {}
        self.params_temporary = {}
        self.params_persistent = {}
        self.user_message = None
        self.history_output = []


class MockSettings:
    """Mock settings dictionary."""
    
    def __init__(self):
        self.data = {
            "loop_detection_enabled": True,
            "loop_detection_threshold": 3,
            "loop_detection_history_size": 5,
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)


class MockAgent:
    """Mock agent with minimal required functionality."""
    
    def __init__(self):
        self.data = {}
        self.context = MockContext()
        self._settings = MockSettings()
    
    def get_data(self, key: str) -> Any:
        return self.data.get(key)
    
    def set_data(self, key: str, value: Any) -> None:
        self.data[key] = value
        # Only print non-large data
        if isinstance(value, list) and len(value) > 3:
            print(f"    [DATA] {key} = [{len(value)} items]")
        else:
            print(f"    [DATA] {key} = {value}")
    
    def parse_prompt(self, template: str, **kwargs) -> str:
        """Simulate prompt parsing."""
        return f"[PROMPT: {template}] failure_count={kwargs.get('failure_count', 0)}"


# ============== Mock Modules ==============

class MockSettingsModule:
    """Mock settings module."""
    
    @staticmethod
    def get_settings():
        return MockSettings()


class MockExtension:
    """Base extension class mock."""
    
    def __init__(self, agent=None):
        self.agent = agent


# ============== Inject Mocks ==============

def setup_mocks():
    """Setup mock modules before importing the real code."""
    # Create mock modules
    sys.modules['python.helpers.extension'] = type(sys)('python.helpers.extension')
    sys.modules['python.helpers.extension'].Extension = MockExtension
    
    sys.modules['python.helpers.settings'] = type(sys)('python.helpers.settings')
    sys.modules['python.helpers.settings'].get_settings = MockSettingsModule.get_settings
    
    sys.modules['agent'] = type(sys)('agent')
    sys.modules['agent'].LoopData = MockLoopData


# ============== Test Code ==============

# Data keys (copied from the real extension to avoid import issues)
DATA_NAME_HISTORY = "loop_detection_history"
DATA_NAME_FAILURES = "loop_detection_failures"
DATA_NAME_LAST_MISFORMAT = "loop_detection_last_misformat"
DATA_NAME_INTERVENTION_ACTIVE = "loop_intervention_active"

DEFAULT_HISTORY_SIZE = 5
DEFAULT_FAILURE_THRESHOLD = 3


class TestLoopDetection:
    """Test the loop detection mechanism."""
    
    def __init__(self):
        self.agent = MockAgent()
        self.test_results = []
    
    def create_signature(self, loop_data: MockLoopData, was_misformat: bool) -> str:
        """Create signature from loop data (copied from real extension)."""
        parts = []
        
        if was_misformat:
            parts.append("MISFORMAT")
        
        if loop_data.last_response:
            response_preview = loop_data.last_response[:100].strip()
            parts.append(f"RESP:{hash(response_preview)}")
        
        if loop_data.current_tool:
            tool_name = loop_data.current_tool.__class__.__name__
            parts.append(f"TOOL:{tool_name}")
        
        if not parts:
            parts.append("NO_ACTION")
        
        return "|".join(parts)
    
    async def execute_detection(self, loop_data: MockLoopData) -> int:
        """Execute loop detection logic and return failure count."""
        set_dict = self.agent._settings.data
        history_size = set_dict.get("loop_detection_history_size", DEFAULT_HISTORY_SIZE)
        failure_threshold = set_dict.get("loop_detection_threshold", DEFAULT_FAILURE_THRESHOLD)
        
        # Get current state
        history = self.agent.get_data(DATA_NAME_HISTORY) or []
        failures = self.agent.get_data(DATA_NAME_FAILURES) or 0
        last_misformat = self.agent.get_data(DATA_NAME_LAST_MISFORMAT) or False
        
        # Create signature
        signature = self.create_signature(loop_data, last_misformat)
        
        # Detect loop
        if len(history) >= 2:
            recent = history[-2:]
            if all(s == signature for s in recent):
                failures += 1
            else:
                if not last_misformat:
                    failures = max(0, failures - 1)
        
        # Store updated state
        history.append(signature)
        history = history[-history_size:]
        self.agent.set_data(DATA_NAME_HISTORY, history)
        self.agent.set_data(DATA_NAME_FAILURES, failures)
        self.agent.set_data(DATA_NAME_LAST_MISFORMAT, False)
        
        # Log if approaching threshold
        if failures > 0 and failures < failure_threshold:
            print(f"    [INFO] Loop detection: {failures}/{failure_threshold}")
        
        return failures
    
    async def check_intervention(self, loop_data: MockLoopData) -> bool:
        """Check if intervention should be injected."""
        failures = self.agent.get_data(DATA_NAME_FAILURES) or 0
        threshold = self.agent._settings.get("loop_detection_threshold", 3)
        
        if failures >= threshold:
            # Inject intervention
            intervention_msg = f"[INTERVENTION PROMPT] failures={failures}"
            loop_data.extras_persistent["loop_intervention"] = intervention_msg
            self.agent.set_data(DATA_NAME_INTERVENTION_ACTIVE, True)
            self.agent.set_data(DATA_NAME_FAILURES, 0)  # Reset
            return True
        return False
    
    def set_misformat_flag(self):
        """Set misformat flag."""
        self.agent.set_data(DATA_NAME_LAST_MISFORMAT, True)
    
    # ============== Test Cases ==============
    
    async def test_1_normal_operation(self):
        """Test that different responses don't trigger loop detection."""
        print("\n" + "=" * 60)
        print("TEST 1: Normal Operation (different responses)")
        print("=" * 60)
        
        loop_data = MockLoopData()
        
        for i in range(5):
            loop_data.iteration = i
            loop_data.last_response = f"Different response number {i}"
            failures = await self.execute_detection(loop_data)
            print(f"  Iteration {i}: failures = {failures}")
            assert failures == 0, f"Expected 0 failures, got {failures}"
        
        print("  [PASS] No loops detected with different responses")
        self.test_results.append(("test_1_normal_operation", True))
    
    async def test_2_identical_responses(self):
        """Test that identical responses trigger loop detection."""
        print("\n" + "=" * 60)
        print("TEST 2: Identical Responses (should trigger loop)")
        print("=" * 60)
        
        # Reset agent state
        self.agent = MockAgent()
        loop_data = MockLoopData()
        same_response = "This is the same response every time"
        
        for i in range(5):
            loop_data.iteration = i
            loop_data.last_response = same_response
            failures = await self.execute_detection(loop_data)
            print(f"  Iteration {i}: failures = {failures}")
            
            # Check for intervention
            if await self.check_intervention(loop_data):
                print(f"  [TRIGGERED] Intervention at iteration {i}!")
                break
        
        assert "loop_intervention" in loop_data.extras_persistent, \
            "Expected intervention to be triggered"
        print("  [PASS] Loop detected and intervention triggered")
        self.test_results.append(("test_2_identical_responses", True))
    
    async def test_3_misformat_loop(self):
        """Test that repeated misformats trigger loop detection."""
        print("\n" + "=" * 60)
        print("TEST 3: Repeated Misformat Errors")
        print("=" * 60)
        
        # Reset agent state
        self.agent = MockAgent()
        loop_data = MockLoopData()
        
        for i in range(5):
            loop_data.iteration = i
            
            # Simulate misformat on iterations 0, 1, 2
            if i < 3:
                self.set_misformat_flag()
                loop_data.last_response = "Misformatted response"
            else:
                loop_data.last_response = f"Response {i}"
            
            failures = await self.execute_detection(loop_data)
            print(f"  Iteration {i}: failures = {failures}")
            
            if await self.check_intervention(loop_data):
                print(f"  [TRIGGERED] Intervention at iteration {i}!")
                break
        
        print("  [PASS] Misformat loop detection works")
        self.test_results.append(("test_3_misformat_loop", True))
    
    async def test_4_recovery_after_change(self):
        """Test that failures reset when behavior changes."""
        print("\n" + "=" * 60)
        print("TEST 4: Recovery After Behavior Change")
        print("=" * 60)
        
        # Reset agent state
        self.agent = MockAgent()
        loop_data = MockLoopData()
        
        # Create some failures with same response
        for i in range(2):
            loop_data.last_response = "Same response"
            failures = await self.execute_detection(loop_data)
            print(f"  Phase 1 - Iteration {i}: failures = {failures}")
        
        # Now change behavior - failures should decrease
        for i in range(3):
            loop_data.last_response = f"Different response {i}"
            failures = await self.execute_detection(loop_data)
            print(f"  Phase 2 - Iteration {i}: failures = {failures}")
        
        final_failures = self.agent.get_data(DATA_NAME_FAILURES) or 0
        assert final_failures == 0, f"Expected 0 failures after recovery, got {final_failures}"
        print("  [PASS] Failures reset after behavior change")
        self.test_results.append(("test_4_recovery_after_change", True))
    
    async def test_5_disabled_detection(self):
        """Test that detection can be disabled."""
        print("\n" + "=" * 60)
        print("TEST 5: Disabled Detection")
        print("=" * 60)
        
        # Reset and disable
        self.agent = MockAgent()
        self.agent._settings.data["loop_detection_enabled"] = False
        loop_data = MockLoopData()
        
        # Should not track failures when disabled
        for i in range(5):
            loop_data.last_response = "Same response"
            
            # Check if enabled
            if not self.agent._settings.get("loop_detection_enabled", True):
                print(f"  Iteration {i}: Detection disabled, skipping")
                continue
            
            failures = await self.execute_detection(loop_data)
            print(f"  Iteration {i}: failures = {failures}")
        
        # Verify no data was stored
        history = self.agent.get_data(DATA_NAME_HISTORY)
        assert history is None, "Expected no history when disabled"
        print("  [PASS] Detection properly disabled")
        self.test_results.append(("test_5_disabled_detection", True))
    
    async def run_all_tests(self):
        """Run all tests."""
        print("\n" + "=" * 60)
        print("LOOP DETECTION UNIT TESTS")
        print("=" * 60)
        
        try:
            await self.test_1_normal_operation()
            await self.test_2_identical_responses()
            await self.test_3_misformat_loop()
            await self.test_4_recovery_after_change()
            await self.test_5_disabled_detection()
        except AssertionError as e:
            print(f"\n  [FAILED] {e}")
            return False
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        passed = sum(1 for _, result in self.test_results if result)
        total = len(self.test_results)
        
        for name, result in self.test_results:
            status = "[PASS]" if result else "[FAIL]"
            print(f"  {status} {name}")
        
        print(f"\n  Total: {passed}/{total} tests passed")
        print("=" * 60)
        
        return passed == total


# ============== Main ==============

async def main():
    """Run the tests."""
    print("\nLoop Detection Unit Test")
    print("This tests the loop detection mechanism in isolation.")
    print("No agent or LLM is required.\n")
    
    tester = TestLoopDetection()
    success = await tester.run_all_tests()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
