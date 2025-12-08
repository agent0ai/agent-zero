# Testing Parallel Agent Delegation

This guide provides step-by-step instructions for testing the parallel agent delegation system.

## Prerequisites

1. **Agent Zero Running**: Ensure Agent Zero is running (Docker or local)
2. **API Keys Configured**: Set up your model API keys in Settings
3. **Web UI Access**: Access to the Agent Zero web interface

## Quick Start Test

### Test 1: Basic Parallel Delegation

**Step 1**: Open Agent Zero web UI and start a new chat

**Step 2**: Send this prompt:
```
I need you to do three independent tasks in parallel:
1. Research best practices for REST API authentication
2. Write a simple Python function to validate email addresses
3. Create a markdown document explaining the difference between GET and POST requests

Use the delegate_parallel tool to do these simultaneously.
```

**Step 3**: Watch the agent's response. You should see:
- Agent recognizing multiple tasks
- Using `delegate_parallel` tool
- Multiple agents working simultaneously
- Results aggregated together

**Expected Behavior**:
- ✅ Agent uses `delegate_parallel` tool
- ✅ Multiple tasks execute in parallel
- ✅ Results are aggregated
- ✅ Faster than sequential execution

### Test 2: Tasks with Dependencies

**Prompt**:
```
I need you to:
1. First, research modern authentication methods for web APIs
2. Then, based on that research, implement a simple authentication function in Python
3. Finally, write unit tests for the authentication function

The implementation depends on the research, and tests depend on the implementation.
Use delegate_parallel with proper dependencies.
```

**Expected Behavior**:
- ✅ Research task starts first
- ✅ Implementation waits for research to complete
- ✅ Tests wait for implementation to complete
- ✅ Dependencies are respected

### Test 3: Verify Parallel Execution

**Prompt**:
```
Create three independent Python scripts:
1. Script 1: Calculate factorial of 10
2. Script 2: Generate first 10 Fibonacci numbers  
3. Script 3: Check if a number is prime

These can all be done in parallel. Use delegate_parallel.
```

**How to Verify**:
- Check the logs/timestamps - tasks should start around the same time
- Results should arrive faster than if done sequentially
- All three scripts should be created

## Manual Testing via Web UI

### Method 1: Direct Tool Usage

You can instruct the agent to use the tool directly:

```
Use the delegate_parallel tool with these tasks:
- Task 1 (developer profile): Write a Python function to sort a list
- Task 2 (researcher profile): Research Python sorting algorithms
- Task 3 (developer profile): Create unit tests for the sort function

Task 3 depends on Task 1.
```

### Method 2: Natural Language Prompt

Let the agent decide to use parallel delegation:

```
I need help with a project. I want you to:
- Research best practices for error handling in Python
- Write a sample error handling module
- Create documentation for the module
- Write unit tests

These tasks can mostly be done in parallel where possible.
```

## Verification Checklist

After running a test, verify:

- [ ] Agent used `delegate_parallel` tool (check tool logs)
- [ ] Multiple agents were spawned (check agent numbers in logs)
- [ ] Tasks executed in parallel (check timestamps)
- [ ] Dependencies were respected (if applicable)
- [ ] Results were aggregated correctly
- [ ] No errors occurred
- [ ] Performance improved vs sequential execution

## Checking Logs

### In Web UI

1. Look for tool execution logs showing `delegate_parallel`
2. Check for multiple agent instances (A1, A2, A3, etc.)
3. Verify task start times are close together for parallel tasks
4. Check that dependent tasks wait for dependencies

### In Console/Logs

If running locally, check console output for:
- `Parallel Delegation Started` messages
- Multiple agent monologues running
- Task completion messages
- Result aggregation messages

## Unit Testing

### Test TaskQueue Directly

Create a test file: `tests/test_task_queue.py`

```python
#!/usr/bin/env python3
"""Test TaskQueue functionality."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from python.helpers.task_queue import TaskQueue, TaskStatus


async def mock_agent_factory(profile=None):
    """Mock agent factory for testing."""
    return {"profile": profile, "id": "mock_agent"}


async def mock_execute_func(agent, message):
    """Mock execute function for testing."""
    await asyncio.sleep(0.1)  # Simulate work
    return f"Result for: {message}"


async def test_basic_parallel_execution():
    """Test basic parallel task execution."""
    queue = TaskQueue(max_concurrent=3)
    
    # Add tasks
    group = queue.add_task_group([
        {"id": "task1", "message": "Task 1"},
        {"id": "task2", "message": "Task 2"},
        {"id": "task3", "message": "Task 3"},
    ])
    
    # Execute
    results = await queue.execute_group(
        group.id,
        mock_agent_factory,
        mock_execute_func
    )
    
    # Verify
    assert len(results) == 3
    assert all(r.get("status") == "completed" for r in results.values())
    print("✅ Basic parallel execution test passed")


async def test_dependency_resolution():
    """Test dependency resolution."""
    queue = TaskQueue(max_concurrent=3)
    
    # Add tasks with dependencies
    group = queue.add_task_group([
        {"id": "task1", "message": "Task 1", "dependencies": []},
        {"id": "task2", "message": "Task 2", "dependencies": ["task1"]},
    ])
    
    # Execute
    results = await queue.execute_group(
        group.id,
        mock_agent_factory,
        mock_execute_func
    )
    
    # Verify task2 waited for task1
    assert results["task1"]["status"] == "completed"
    assert results["task2"]["status"] == "completed"
    print("✅ Dependency resolution test passed")


if __name__ == "__main__":
    asyncio.run(test_basic_parallel_execution())
    asyncio.run(test_dependency_resolution())
    print("\n✅ All tests passed!")
```

Run with:
```bash
python tests/test_task_queue.py
```

## Integration Testing

### Test with Real Agents

Create: `tests/test_delegate_parallel_integration.py`

```python
#!/usr/bin/env python3
"""Integration test for parallel delegation."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from agent import Agent, AgentContext, AgentConfig
from initialize import initialize_agent
from python.tools.delegate_parallel import DelegateParallel


async def test_parallel_delegation():
    """Test parallel delegation with real agents."""
    config = initialize_agent()
    context = AgentContext(config=config)
    agent = Agent(0, config, context)
    
    # Create tool instance
    tool = DelegateParallel(
        agent=agent,
        name="delegate_parallel",
        method=None,
        args={},
        message="",
        loop_data=None
    )
    
    # Test with simple tasks
    tasks = [
        {
            "id": "task1",
            "message": "Write a Python function that returns 'Hello'",
            "dependencies": []
        },
        {
            "id": "task2",
            "message": "Write a Python function that returns 'World'",
            "dependencies": []
        }
    ]
    
    response = await tool.execute(tasks=tasks, wait_for_all=True)
    
    assert response.message is not None
    assert "task1" in response.message or "task2" in response.message
    print("✅ Integration test passed")


if __name__ == "__main__":
    asyncio.run(test_parallel_delegation())
```

## Performance Testing

### Compare Sequential vs Parallel

**Sequential Test**:
```
Use call_subordinate three times sequentially:
1. Research topic A
2. Research topic B  
3. Research topic C
```

**Parallel Test**:
```
Use delegate_parallel to research topics A, B, and C simultaneously
```

**Measure**:
- Total execution time
- Time to first result
- Resource usage

**Expected**: Parallel should be faster (roughly 1/3 the time for 3 independent tasks)

## Troubleshooting

### Issue: Tool Not Found

**Symptom**: Agent says it can't find `delegate_parallel` tool

**Solution**:
1. Check that `python/tools/delegate_parallel.py` exists
2. Check that `prompts/agent.system.tool.delegate_parallel.md` exists
3. Restart Agent Zero
4. Check tool registration in logs

### Issue: Tasks Not Running in Parallel

**Symptom**: Tasks execute sequentially despite using `delegate_parallel`

**Solution**:
1. Check `max_concurrent` setting in TaskQueue
2. Verify tasks don't have blocking dependencies
3. Check for resource constraints
4. Look for errors in logs

### Issue: Dependencies Not Working

**Symptom**: Dependent tasks start before dependencies complete

**Solution**:
1. Verify task IDs match exactly
2. Check dependency graph in logs
3. Ensure dependencies are specified correctly
4. Check TaskQueue dependency resolution logic

### Issue: Results Not Aggregated

**Symptom**: Results are missing or incomplete

**Solution**:
1. Check task completion status
2. Verify all tasks completed successfully
3. Check result aggregation logic
4. Look for errors in individual tasks

## Debug Mode

### Enable Verbose Logging

Add to your test:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Task Queue Status

Add debug output:
```python
status = task_queue.get_group_status(group_id)
print(f"Group status: {status}")
```

### Monitor Agent Creation

Add logging to agent factory:
```python
def create_agent(profile):
    print(f"Creating agent with profile: {profile}")
    # ... agent creation
```

## Example Test Scenarios

### Scenario 1: Simple Parallel Tasks
```
Research three different topics simultaneously:
- Topic A: Python async programming
- Topic B: REST API design
- Topic C: Database optimization
```

### Scenario 2: Complex Dependencies
```
1. Research authentication methods
2. Design authentication system (depends on 1)
3. Implement authentication (depends on 2)
4. Write tests (depends on 3)
5. Write documentation (depends on 2)
```

### Scenario 3: Mixed Independent and Dependent
```
Independent tasks:
- Research topic A
- Research topic B
- Write utility function

Dependent task:
- Integrate everything (depends on all above)
```

## Success Criteria

A successful test should demonstrate:

1. ✅ **Functionality**: Tool works as expected
2. ✅ **Performance**: Faster than sequential execution
3. ✅ **Reliability**: Handles errors gracefully
4. ✅ **Correctness**: Dependencies respected
5. ✅ **Usability**: Easy to use via natural language

## Next Steps

After successful testing:

1. **Performance Tuning**: Adjust `max_concurrent` based on your resources
2. **Error Handling**: Test various failure scenarios
3. **Integration**: Use in real workflows
4. **Monitoring**: Add metrics and monitoring
5. **Documentation**: Document best practices

## Getting Help

If you encounter issues:

1. Check the logs for error messages
2. Verify all files are in place
3. Test with simpler scenarios first
4. Check the implementation documentation
5. Review the code for potential issues

