### todo

This tool helps you manage a to-do list to keep track of your tasks.

**Methods:**

*   `add(task: str)`: Adds a new task to your to-do list.
*   `update(task_id: str, status: str)`: Updates the status of a task. The status can be `todo`, `in_progress`, or `done`.
*   `list()`: Shows all the tasks in your to-do list with their IDs and statuses.
*   `next()`: Gets the next task that needs to be done (i.e., the first task with the status `todo`).

**Example Usage:**

To add a new task:
~~~json
{
    "thoughts": [
        "I need to start by outlining the new feature.",
        "I'll add this as a task to my to-do list."
    ],
    "tool_name": "todo:add",
    "tool_args": {
        "task": "Outline the new feature"
    }
}
~~~

To see the list of tasks:
~~~json
{
    "thoughts": [
        "I should check what's on my to-do list."
    ],
    "tool_name": "todo:list",
    "tool_args": {}
}
~~~

To update a task's status:
~~~json
{
    "thoughts": [
        "I have started working on the outline.",
        "I'll update the status of the task to 'in_progress'."
    ],
    "tool_name": "todo:update",
    "tool_args": {
        "task_id": "a1b2c3d4",
        "status": "in_progress"
    }
}
~~~
