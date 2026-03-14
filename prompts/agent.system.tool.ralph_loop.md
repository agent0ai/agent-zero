# Ralph Loop Tool

Autonomous iterative task execution using the Ralph Wiggum technique.

Ralph Loop enables Agent Jumbo to work on tasks iteratively, continuing until the task is complete or a maximum number of iterations is reached. This is ideal for complex tasks that require multiple attempts, refinement, or tasks where success criteria can be automatically verified.

## How It Works

1. **Start a loop** with a prompt and completion criteria
2. **Agent works** on the task, with changes persisting in files
3. **Iteration continues** automatically until:
   - Completion promise is output (task done)
   - Max iterations reached (safety limit)
   - Manual cancellation

## Quick Start

```
{{ralph_loop(
  action="start_loop",
  name="Implement Feature",
  prompt="Create a REST API for user management with full CRUD operations and unit tests. Follow TDD approach.",
  completion_promise="ALL_TESTS_PASSING",
  max_iterations=30
)}}
```

## Available Actions

### Loop Lifecycle

#### start_loop

Start a new Ralph loop.

```
{{ralph_loop(
  action="start_loop",
  name="Task Name",
  prompt="Detailed task description...",
  completion_promise="DONE",
  max_iterations=50
)}}
```

**Parameters:**

- `name` (optional): Name for the loop
- `prompt` (required): Task description and instructions
- `completion_promise` (optional): Text to output when task is complete
- `max_iterations` (optional, default 50): Safety limit

#### get_status

Check current loop status.

```
{{ralph_loop(action="get_status", loop_id=1)}}
```

If `loop_id` is omitted, returns status of the active loop for the current agent.

#### cancel_loop

Cancel an active loop.

```
{{ralph_loop(action="cancel_loop", loop_id=1, reason="Need to change approach")}}
```

#### list_loops

List Ralph loops.

```
{{ralph_loop(action="list_loops", status="active")}}
```

**Parameters:**

- `status` (optional): Filter by status (active, completed, cancelled, paused)
- `limit` (optional, default 20): Max results

#### get_loop_history

View iteration history.

```
{{ralph_loop(action="get_loop_history", loop_id=1)}}
```

### Workflow Integration

#### start_task_loop

Start a Ralph loop for a workflow task.

```
{{ralph_loop(
  action="start_task_loop",
  workflow_execution_id=1,
  task_id="implement_core",
  prompt="Implement the core features. Run tests until all pass.",
  completion_promise="TESTS_GREEN",
  max_iterations=30
)}}
```

#### link_to_workflow

Link an existing loop to a workflow execution.

```
{{ralph_loop(
  action="link_to_workflow",
  loop_id=1,
  workflow_execution_id=1,
  task_id="implement_core"
)}}
```

### Configuration

#### set_completion_promise

Update the completion promise mid-loop.

```
{{ralph_loop(action="set_completion_promise", loop_id=1, completion_promise="NEW_CRITERIA")}}
```

#### set_max_iterations

Update the iteration limit.

```
{{ralph_loop(action="set_max_iterations", loop_id=1, max_iterations=100)}}
```

#### pause_loop

Pause an active loop (can resume later).

```
{{ralph_loop(action="pause_loop", loop_id=1)}}
```

#### resume_loop

Resume a paused loop.

```
{{ralph_loop(action="resume_loop", loop_id=1)}}
```

### Statistics

#### get_stats

View Ralph loop statistics.

```
{{ralph_loop(action="get_stats")}}
```

## Completion Promise

The completion promise is how the loop knows when a task is done. When you complete the task, output:

```
<promise>YOUR_COMPLETION_PROMISE</promise>
```

For example, if your promise is `ALL_TESTS_PASSING`, output:

```
<promise>ALL_TESTS_PASSING</promise>
```

**Important Rules:**

- Only output the promise when the task is **genuinely complete**
- Do not lie to exit the loop early
- The promise text must match exactly (case-insensitive)

## Best Practices

### Good Prompts

✅ Clear completion criteria:

```
{{ralph_loop(
  action="start_loop",
  prompt="Build a REST API for todos with:
    - CRUD endpoints (GET, POST, PUT, DELETE)
    - Input validation
    - Unit tests with >80% coverage

    When ALL requirements are met, output <promise>COMPLETE</promise>",
  completion_promise="COMPLETE",
  max_iterations=50
)}}
```

✅ Incremental goals:

```
{{ralph_loop(
  action="start_loop",
  prompt="Phase 1: Create database schema
    Phase 2: Implement models
    Phase 3: Add API endpoints
    Phase 4: Write tests

    Output <promise>ALL_PHASES_DONE</promise> when complete",
  completion_promise="ALL_PHASES_DONE",
  max_iterations=40
)}}
```

✅ Self-correction instructions:

```
{{ralph_loop(
  action="start_loop",
  prompt="Implement feature X following TDD:
    1. Write failing tests
    2. Implement feature
    3. Run tests
    4. If tests fail, debug and fix
    5. Repeat until all tests pass

    Output <promise>TESTS_PASSING</promise> when all tests green",
  completion_promise="TESTS_PASSING",
  max_iterations=30
)}}
```

### Avoid

❌ Vague prompts:

```
# Bad - no clear success criteria
{{ralph_loop(prompt="Make the code better")}}
```

❌ Impossible tasks:

```
# Bad - no clear path to completion
{{ralph_loop(prompt="Write perfect code with no bugs")}}
```

## AI Solutioning Integration

Ralph Loop integrates with the AI Solutioning workflow:

| Workflow Stage | Ralph Usage |
|----------------|-------------|
| POC | Iterate until demo works |
| Implementation | Iterate until tests pass |
| Deployment | Iterate until health checks green |
| Optimization | Iterate prompt refinement |

## Safety Features

1. **Max Iterations**: Hard limit prevents infinite loops
2. **Manual Override**: Can always cancel via tool or UI
3. **File Persistence**: Work saved between iterations
4. **Git Integration**: Optional commit after each iteration

## Example: Building a Feature

```
# Start the loop
{{ralph_loop(
  action="start_loop",
  name="User Authentication",
  prompt="Implement JWT authentication:

    Requirements:
    1. Login endpoint (/api/auth/login)
    2. Logout endpoint (/api/auth/logout)
    3. Token refresh (/api/auth/refresh)
    4. Protected route middleware
    5. Unit tests for all endpoints
    6. Integration tests for auth flow

    Process:
    - Use TDD approach
    - Run tests after each change
    - Fix any failures before proceeding

    When all tests pass and requirements met:
    <promise>AUTH_COMPLETE</promise>",
  completion_promise="AUTH_COMPLETE",
  max_iterations=50
)}}

# Check progress
{{ralph_loop(action="get_status")}}

# If stuck, can cancel
{{ralph_loop(action="cancel_loop", reason="Need different approach")}}
```
