### call_subordinate

This tool allows you to delegate a task to a subordinate agent. You can provide a detailed description of the task using the parameters below.

**Arguments:**

*   `task` (string, required): A clear and concise description of the task for the subordinate.
*   `objectives` (list of strings, optional): A list of specific objectives the subordinate should achieve.
*   `parent_task` (string, optional): The main task you are working on.
*   `context` (string, optional): Any relevant context or background information for the task.
*   `scopes` (list of strings, optional): A list of what is in scope for the task.
*   `non_goals` (list of strings, optional): A list of what is out of scope for the task.
*   `success_criteria` (list of strings, optional): A list of criteria that define success for the task.
*   `errors_to_avoid` (list of strings, optional): A list of potential errors or pitfalls to avoid.
*   `reset` (string, optional): Set to "true" to spawn a new subordinate, or "false" to continue with an existing one. Defaults to "false".
*   `prompt_profile` (string, optional): The name of the prompt profile to use for the subordinate (e.g., "coder", "researcher").

**Example Usage:**

~~~json
{
    "thoughts": [
        "I need to create a new module for user authentication.",
        "I will delegate this task to a coder subordinate with specific instructions."
    ],
    "tool_name": "call_subordinate",
    "tool_args": {
        "task": "Implement a user authentication module.",
        "prompt_profile": "coder",
        "objectives": [
            "Create a login page with username and password fields.",
            "Implement session management using JWT.",
            "Add password hashing for security."
        ],
        "parent_task": "Develop a new e-commerce website.",
        "success_criteria": [
            "Users can successfully log in and out.",
            "Passwords are securely stored.",
            "A valid JWT is generated upon login."
        ],
        "reset": "true"
    }
}
~~~