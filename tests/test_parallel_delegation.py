#!/usr/bin/env python3
"""
Test script for parallel agent delegation functionality.

Run with: python tests/test_parallel_delegation.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime
from python.helpers.task_queue import TaskQueue


async def mock_agent_factory(profile=None):
    """Mock agent factory for testing."""
    class MockAgent:
        def __init__(self, profile):
            self.profile = profile
            self.id = f"agent_{profile or 'default'}"
    return MockAgent(profile)


async def mock_execute_func(agent, message):
    """Mock execute function that simulates work."""
    # Simulate some work
    await asyncio.sleep(0.1)
    return f"Completed: {message} (by {agent.id})"


async def test_basic_parallel_execution():
    """Test that tasks execute in parallel."""
    print("\n🧪 Test 1: Basic Parallel Execution")
    print("-" * 50)
    
    queue = TaskQueue(max_concurrent=3)
    
    # Add three independent tasks
    group = queue.add_task_group([
        {"id": "task1", "message": "Task 1 - Research"},
        {"id": "task2", "message": "Task 2 - Code"},
        {"id": "task3", "message": "Task 3 - Test"},
    ])
    
    start_time = datetime.now()
    results = await queue.execute_group(
        group.id,
        mock_agent_factory,
        mock_execute_func
    )
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Verify all tasks completed
    assert len(results) == 3, f"Expected 3 results, got {len(results)}"
    assert all(r.get("status") == "completed" for r in results.values()), "Not all tasks completed"
    
    # Verify parallel execution (should be faster than sequential)
    # Sequential would take ~0.3s, parallel should take ~0.1s
    assert duration < 0.2, f"Tasks took {duration}s, expected <0.2s for parallel execution"
    
    print(f"✅ All tasks completed in {duration:.2f}s")
    print(f"   Results: {list(results.keys())}")


async def test_dependency_resolution():
    """Test that dependencies are respected."""
    print("\n🧪 Test 2: Dependency Resolution")
    print("-" * 50)
    
    queue = TaskQueue(max_concurrent=3)
    
    # Add tasks with dependencies
    group = queue.add_task_group([
        {"id": "task1", "message": "Research", "dependencies": []},
        {"id": "task2", "message": "Implement", "dependencies": ["task1"]},
        {"id": "task3", "message": "Test", "dependencies": ["task2"]},
    ])
    
    execution_order = []
    
    async def track_execute_func(agent, message):
        execution_order.append(message)
        await asyncio.sleep(0.05)
        return f"Done: {message}"
    
    await queue.execute_group(
        group.id,
        mock_agent_factory,
        track_execute_func
    )
    
    # Verify execution order
    assert "Research" in execution_order[0], "Research should execute first"
    assert "Implement" in execution_order[1], "Implement should execute second"
    assert "Test" in execution_order[2], "Test should execute third"
    
    print("✅ Dependencies respected")
    print(f"   Execution order: {execution_order}")


async def test_mixed_independent_dependent():
    """Test mix of independent and dependent tasks."""
    print("\n🧪 Test 3: Mixed Independent and Dependent Tasks")
    print("-" * 50)
    
    queue = TaskQueue(max_concurrent=3)
    
    # Independent tasks + dependent task
    group = queue.add_task_group([
        {"id": "task1", "message": "Research A", "dependencies": []},
        {"id": "task2", "message": "Research B", "dependencies": []},
        {"id": "task3", "message": "Integrate", "dependencies": ["task1", "task2"]},
    ])
    
    start_time = datetime.now()
    results = await queue.execute_group(
        group.id,
        mock_agent_factory,
        mock_execute_func
    )
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Verify all completed
    assert len(results) == 3
    assert all(r.get("status") == "completed" for r in results.values())
    
    # Task3 should start after task1 and task2 complete
    # So total time should be ~0.1s (task1/task2 parallel) + ~0.1s (task3) = ~0.2s
    assert 0.15 < duration < 0.3, f"Duration {duration}s not in expected range"
    
    print(f"✅ Mixed tasks completed in {duration:.2f}s")
    print(f"   Independent tasks ran in parallel, dependent task waited")


async def test_error_handling():
    """Test error handling for failed tasks."""
    print("\n🧪 Test 4: Error Handling")
    print("-" * 50)
    
    queue = TaskQueue(max_concurrent=2)
    
    async def failing_execute_func(agent, message):
        if "fail" in message.lower():
            raise Exception(f"Task failed: {message}")
        await asyncio.sleep(0.05)
        return f"Success: {message}"
    
    group = queue.add_task_group([
        {"id": "task1", "message": "Success task"},
        {"id": "task2", "message": "Fail task"},
    ])
    
    results = await queue.execute_group(
        group.id,
        mock_agent_factory,
        failing_execute_func
    )
    
    # Verify one succeeded, one failed
    assert results["task1"]["status"] == "completed"
    assert results["task2"]["status"] == "failed"
    assert "error" in results["task2"]
    
    print("✅ Error handling works correctly")
    print(f"   Task 1: {results['task1']['status']}")
    print(f"   Task 2: {results['task2']['status']}")


async def test_concurrent_limit():
    """Test that concurrent limit is respected."""
    print("\n🧪 Test 5: Concurrent Limit")
    print("-" * 50)
    
    queue = TaskQueue(max_concurrent=2)  # Limit to 2 concurrent
    
    active_tasks = []
    max_active = 0
    
    async def track_execute_func(agent, message):
        active_tasks.append(message)
        nonlocal max_active
        max_active = max(max_active, len(active_tasks))
        await asyncio.sleep(0.1)
        active_tasks.remove(message)
        return f"Done: {message}"
    
    # Add 5 tasks
    group = queue.add_task_group([
        {"id": f"task{i}", "message": f"Task {i}"} for i in range(5)
    ])
    
    await queue.execute_group(
        group.id,
        mock_agent_factory,
        track_execute_func
    )
    
    # Should never exceed max_concurrent
    assert max_active <= 2, f"Max concurrent tasks {max_active} exceeds limit of 2"
    
    print(f"✅ Concurrent limit respected (max active: {max_active})")


async def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Testing Parallel Agent Delegation")
    print("=" * 60)
    
    try:
        await test_basic_parallel_execution()
        await test_dependency_resolution()
        await test_mixed_independent_dependent()
        await test_error_handling()
        await test_concurrent_limit()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

