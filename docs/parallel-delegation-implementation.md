# Parallel Agent Delegation Implementation

## Overview

This document describes the implementation of parallel agent delegation for Agent Zero, allowing multiple agents to work simultaneously on different subtasks with proper dependency management and resource coordination.

## Architecture

### Components

1. **TaskQueue** (`python/helpers/task_queue.py`)
   - Manages parallel task execution
   - Handles dependency resolution
   - Coordinates resource allocation
   - Tracks task status and results

2. **RequirementsAnalyzer** (`python/helpers/requirements_analyzer.py`)
   - Analyzes user prompts to extract requirements
   - Identifies parallelizable tasks
   - Suggests appropriate agent profiles
   - Creates task dependency graphs

3. **DelegateParallel Tool** (`python/tools/delegate_parallel.py`)
   - New tool for parallel delegation
   - Replaces sequential `call_subordinate` calls
   - Manages agent lifecycle
   - Aggregates results

## How It Works

### Basic Flow

```
User Prompt
    ↓
Agent 0 analyzes prompt
    ↓
Identifies parallelizable tasks
    ↓
Calls delegate_parallel tool
    ↓
TaskQueue creates task group
    ↓
Spawns multiple agents in parallel
    ↓
Respects dependencies
    ↓
Aggregates results
    ↓
Returns to Agent 0
```

### Task Execution

1. **Task Creation**: Tasks are added to the queue with dependencies
2. **Dependency Resolution**: Tasks wait for dependencies to complete
3. **Parallel Execution**: Ready tasks execute concurrently (up to max_concurrent limit)
4. **Result Collection**: Results are collected and aggregated
5. **Error Handling**: Failed tasks are reported but don't block others

### Dependency Management

Tasks can depend on other tasks:
- Dependencies are specified as a list of task IDs
- Tasks wait for all dependencies to complete before starting
- Circular dependencies are prevented
- Failed dependencies cause dependent tasks to fail

## Usage

### Basic Example

```json
{
    "tool_name": "delegate_parallel",
    "tool_args": {
        "tasks": [
            {
                "id": "task1",
                "profile": "developer",
                "message": "Write unit tests for authentication",
                "dependencies": []
            },
            {
                "id": "task2",
                "profile": "researcher",
                "message": "Research API security best practices",
                "dependencies": []
            }
        ],
        "wait_for_all": true
    }
}
```

### With Dependencies

```json
{
    "tool_name": "delegate_parallel",
    "tool_args": {
        "tasks": [
            {
                "id": "research",
                "profile": "researcher",
                "message": "Research authentication methods",
                "dependencies": []
            },
            {
                "id": "implement",
                "profile": "developer",
                "message": "Implement based on research",
                "dependencies": ["research"]
            }
        ],
        "wait_for_all": true
    }
}
```

## Configuration

### TaskQueue Settings

The `TaskQueue` can be configured with:
- `max_concurrent`: Maximum number of tasks to run concurrently (default: 5)

```python
task_queue = TaskQueue(max_concurrent=10)
```

### Per-Context Queue

Each `AgentContext` gets its own `TaskQueue` instance:
- Isolated task execution per context
- Prevents resource conflicts
- Allows independent task management

## Integration Points

### Agent Context

The task queue is attached to `AgentContext`:
```python
if not hasattr(self.agent.context, '_task_queue'):
    self.agent.context._task_queue = TaskQueue(max_concurrent=5)
```

### Agent Creation

Agents are created using the same factory pattern as `call_subordinate`:
- Uses `initialize_agent()` for configuration
- Supports profile selection
- Maintains superior/subordinate relationships

### Tool Registration

The tool is automatically discovered:
- File: `python/tools/delegate_parallel.py`
- Prompt: `prompts/agent.system.tool.delegate_parallel.md`
- Variables: `prompts/agent.system.tool.delegate_parallel.py`

## Benefits

1. **Performance**: Parallel execution reduces total time
2. **Efficiency**: Better resource utilization
3. **Scalability**: Handle complex multi-faceted tasks
4. **Reliability**: Better error handling and recovery
5. **User Experience**: Faster responses for complex tasks

## Limitations

1. **Resource Constraints**: Limited by API rate limits and system resources
2. **Complexity**: More complex than sequential delegation
3. **Debugging**: Harder to debug parallel execution
4. **Result Quality**: Requires careful aggregation

## Future Enhancements

1. **Requirements Analyzer Integration**: Automatic task decomposition
2. **Resource Monitoring**: Track and limit resource usage
3. **Agent Pooling**: Reuse agents for similar tasks
4. **Priority Scheduling**: Support task priorities
5. **Progress Tracking**: Real-time progress updates
6. **Result Caching**: Cache results for similar tasks

## Testing

To test the parallel delegation:

1. Create a prompt with multiple independent tasks
2. Use `delegate_parallel` tool
3. Verify tasks execute in parallel
4. Check dependency resolution works
5. Verify result aggregation

Example test prompt:
```
"Research API security best practices, write unit tests for authentication, 
and create documentation. These can be done in parallel."
```

## Migration from call_subordinate

The new `delegate_parallel` tool can be used alongside `call_subordinate`:
- Use `call_subordinate` for single sequential tasks
- Use `delegate_parallel` for multiple parallel tasks
- Both tools can be used in the same conversation

## Docker Considerations

The parallel delegation system works within the existing Docker container:
- No additional container requirements
- Uses existing agent infrastructure
- Respects container resource limits
- Can be scaled by adjusting `max_concurrent`

## Troubleshooting

### Tasks Not Running in Parallel

- Check `max_concurrent` setting
- Verify tasks don't have blocking dependencies
- Check for resource constraints

### Dependency Issues

- Verify task IDs match exactly
- Check for circular dependencies
- Ensure dependencies complete successfully

### Resource Exhaustion

- Reduce `max_concurrent` limit
- Check API rate limits
- Monitor memory usage

## API Reference

### TaskQueue

```python
class TaskQueue:
    def __init__(self, max_concurrent: int = 5)
    def add_task(task_id, message, profile=None, dependencies=None, metadata=None)
    def add_task_group(tasks, wait_for_all=True, timeout=None)
    async def execute_group(group_id, agent_factory, execute_func)
    def get_task_status(task_id)
    def get_group_status(group_id)
```

### DelegateParallel Tool

```python
class DelegateParallel(Tool):
    async def execute(tasks, wait_for_all=True, timeout=None)
```

## Examples

See `docs/parallel-agent-delegation.md` for detailed examples and use cases.

