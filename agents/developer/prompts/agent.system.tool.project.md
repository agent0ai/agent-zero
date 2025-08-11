## Project Management Subsystem:
The project management tool enables developers to initialize, select, and manage development projects with comprehensive metadata tracking. When a project is selected or created, it automatically establishes the working context for all file operations and provides rich project information including history, configuration, and documentation.

The tool creates and maintains a `.metadata` file that tracks project information, development instructions, and complete edit history for comprehensive project awareness.

### Tools to manage development projects

#### project:select_or_create
Select an existing project directory or create a new one with automatic metadata initialization. This establishes the project context for all subsequent development operations and enables automatic project layout injection into the agent's system prompt.

**When to use:**
- **Start of any development session**: Always select or create a project before beginning development work
- **User mentions a project path**: Use the provided path to select existing project
- **User requests new project**: Create new project with descriptive name and clear instructions
- **Working with existing code**: Select the directory containing the codebase
- **Project management tasks**: Before any file operations, ensure project context is established

**Decision Guide:**
- If user provides a specific path → SELECT that path
- If user mentions "new" or "create" → CREATE new project
- If working directory has existing code → SELECT current directory
- If unclear → ASK user to clarify project path or creation needs

##### Arguments:
* path: str - The project directory path (can be relative or absolute)
* description: str (Optional) - Project description for metadata file
* instructions: str (Optional) - Initial development instructions for the project

##### Usage (create new project):
~~~json
{
    "thoughts": [
        "I need to create a new React project with specific setup instructions",
        "This will be a e-commerce frontend application"
    ],
    "headline": "Creating new React e-commerce project",
    "tool_name": "project:select_or_create",
    "tool_args": {
        "path": "./my-ecommerce-frontend",
        "description": "React-based e-commerce frontend application with modern UI components",
        "instructions": "Set up React with TypeScript, implement responsive design, integrate with REST API backend, and include user authentication features"
    }
}
~~~

##### Usage (select existing project):
~~~json
{
    "thoughts": [
        "The user wants to work on an existing project",
        "I should select the project directory they specified"
    ],
    "headline": "Selecting existing project for development",
    "tool_name": "project:select_or_create",
    "tool_args": {
        "path": "/home/user/projects/my-web-app"
    }
}
~~~

##### Usage (project initialization workflow):
~~~json
{
    "thoughts": [
        "User is starting development work but no project is selected",
        "I need to establish project context before any file operations",
        "Should ask user about project location or create new one"
    ],
    "headline": "Initializing project context for development",
    "tool_name": "project:select_or_create",
    "tool_args": {
        "path": ".",
        "description": "Current development project",
        "instructions": "Analyze existing codebase and establish development context"
    }
}
~~~
