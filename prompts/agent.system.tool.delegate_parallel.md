### delegate_parallel

Use this tool to delegate multiple tasks to subordinate agents in parallel. This is more efficient than calling `call_subordinate` multiple times sequentially.

**When to use:**
- You have multiple independent subtasks that can be worked on simultaneously
- Tasks have dependencies that need to be respected
- You want to speed up execution by parallelizing work
- You need to coordinate multiple specialized agents

**Key features:**
- Execute multiple tasks in parallel
- Handle task dependencies automatically
- Aggregate results from all tasks
- Support for different agent profiles per task
- Graceful error handling for individual tasks

**Task structure:**
Each task in the `tasks` array should have:
- `id`: Unique identifier for the task (required)
- `message`: Task description/instructions (required)
- `profile`: Agent profile to use (optional, e.g., "developer", "researcher", "hacker")
- `dependencies`: List of task IDs this task depends on (optional)
- `metadata`: Additional metadata (optional)

**Dependencies:**
- Tasks with dependencies will wait for their dependencies to complete
- Dependencies are specified as a list of task IDs
- Circular dependencies are not allowed

**Example usage - Independent tasks:**
~~~json
{
    "thoughts": [
        "I need to research API security and write unit tests simultaneously",
        "These tasks are independent and can run in parallel"
    ],
    "tool_name": "delegate_parallel",
    "tool_args": {
        "tasks": [
            {
                "id": "research_task",
                "profile": "researcher",
                "message": "Research best practices for REST API security authentication",
                "dependencies": []
            },
            {
                "id": "test_task",
                "profile": "developer",
                "message": "Write comprehensive unit tests for the authentication module",
                "dependencies": []
            }
        ],
        "wait_for_all": true
    }
}
~~~

**Example usage - Tasks with dependencies:**
~~~json
{
    "thoughts": [
        "First I need to research, then implement based on findings",
        "The implementation depends on the research results"
    ],
    "tool_name": "delegate_parallel",
    "tool_args": {
        "tasks": [
            {
                "id": "research",
                "profile": "researcher",
                "message": "Research modern authentication methods for web APIs",
                "dependencies": []
            },
            {
                "id": "implement",
                "profile": "developer",
                "message": "Implement authentication system based on research findings",
                "dependencies": ["research"]
            }
        ],
        "wait_for_all": true
    }
}
~~~

**Example usage - Complex parallel workflow:**
~~~json
{
    "thoughts": [
        "I need to break this into multiple parallel tasks",
        "Some tasks can run immediately, others depend on earlier results"
    ],
    "tool_name": "delegate_parallel",
    "tool_args": {
        "tasks": [
            {
                "id": "task1",
                "profile": "researcher",
                "message": "Research user authentication best practices",
                "dependencies": []
            },
            {
                "id": "task2",
                "profile": "developer",
                "message": "Write unit tests for existing auth code",
                "dependencies": []
            },
            {
                "id": "task3",
                "profile": "developer",
                "message": "Implement improvements based on research",
                "dependencies": ["task1"]
            },
            {
                "id": "task4",
                "profile": "developer",
                "message": "Integrate and test the complete solution",
                "dependencies": ["task2", "task3"]
            }
        ],
        "wait_for_all": true,
        "timeout": 3600
    }
}
~~~

**Parameters:**
- `tasks`: Array of task objects (required)
- `wait_for_all`: Whether to wait for all tasks to complete before returning (default: true)
- `timeout`: Maximum time to wait in seconds (optional, default: no timeout)

**Response handling:**
- Results from all completed tasks are aggregated
- Failed tasks are reported separately
- Use `§§include(<path>)` to include detailed results from individual tasks
- The aggregated response includes a summary of all tasks

**Best practices:**
- Use parallel delegation for independent or loosely coupled tasks
- Keep task descriptions clear and specific
- Use appropriate agent profiles for each task type
- Set reasonable dependencies to ensure correct execution order
- Consider using `wait_for_all: false` if you only need some tasks to complete

**available profiles:**
{{agent_profiles}}

