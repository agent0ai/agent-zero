## Git Version Control Subsystem:
The Git tool enables developers to maintain proper version control with automatic repository initialization and systematic commit workflows. Every project MUST be under Git version control with meaningful commit messages documenting development progress.

The tool automatically configures repositories with standard .gitignore files and ensures proper commit hygiene throughout the development lifecycle.

### Git Workflow Requirements

**MANDATORY GIT WORKFLOW:**
1. **Repository Initialization**: Every new project MUST have Git initialized immediately after creation
2. **Commit Frequency**: EVERY significant change requires a commit with a meaningful message
3. **Commit Messages**: Must be descriptive and follow conventional format (see examples below)
4. **Change Tracking**: Always check Git status before and after major operations

**When to Commit:**
- After creating/modifying any file
- After implementing a feature or fixing a bug
- After refactoring or code cleanup
- Before switching to a different task
- At logical development milestones

### Tools for Git version control

#### git:init
Initialize a Git repository with automatic configuration and initial commit. Creates .gitignore file and commits all initial files.

##### Arguments:
* path: str (Optional) - Repository path (defaults to current project path)
* message: str (Optional) - Initial commit message (default: "Initial commit")

##### Usage:
~~~json
{
    "thoughts": [
        "New project created, need to initialize Git repository",
        "This will create .gitignore and make initial commit"
    ],
    "headline": "Initializing Git repository for project",
    "tool_name": "git:init",
    "tool_args": {
        "message": "Initial project setup with basic structure"
    }
}
~~~

#### git:commit
Commit changes to the repository with a meaningful message. Automatically stages all changes unless specified otherwise.

##### Arguments:
* message: str (Required) - Descriptive commit message
* path: str (Optional) - Repository path (defaults to current project path)
* add_all: bool (Optional) - Whether to add all changed files before committing (default: true)

##### Usage Examples:
~~~json
{
    "thoughts": [
        "Implemented user authentication feature",
        "Need to commit these changes with descriptive message"
    ],
    "headline": "Committing authentication implementation",
    "tool_name": "git:commit",
    "tool_args": {
        "message": "feat: implement user authentication with JWT tokens"
    }
}
~~~

~~~json
{
    "thoughts": [
        "Fixed critical bug in file validation",
        "This resolves the line number out of range issue"
    ],
    "headline": "Committing bug fix",
    "tool_name": "git:commit",
    "tool_args": {
        "message": "fix: resolve line number validation for empty files"
    }
}
~~~

~~~json
{
    "thoughts": [
        "Files are already staged, just need to commit",
        "Using add_all: false since files are already in staging"
    ],
    "headline": "Committing pre-staged changes",
    "tool_name": "git:commit",
    "tool_args": {
        "message": "refactor: reorganize utility functions",
        "add_all": false
    }
}
~~~

#### git:status
Check the current Git repository status to see uncommitted changes.

##### Usage:
~~~json
{
    "thoughts": [
        "Need to check what files have been modified",
        "This will show me current repository state"
    ],
    "headline": "Checking Git repository status",
    "tool_name": "git:status",
    "tool_args": {}
}
~~~

#### git:add
Add specific files to the Git staging area.

##### Arguments:
* files: str|list (Optional) - Files to add (default: "." for all files)
* path: str (Optional) - Repository path (defaults to current project path)

##### Usage:
~~~json
{
    "thoughts": [
        "Need to stage specific files before committing",
        "Adding only the modified configuration files"
    ],
    "headline": "Adding specific files to Git staging",
    "tool_name": "git:add",
    "tool_args": {
        "files": ["config.json", "src/main.py"]
    }
}
~~~

#### git:log
View recent commit history.

##### Arguments:
* limit: int (Optional) - Number of commits to show (default: 10)
* path: str (Optional) - Repository path (defaults to current project path)

##### Usage:
~~~json
{
    "thoughts": [
        "Need to review recent changes to understand project history",
        "This will show the last 5 commits"
    ],
    "headline": "Viewing recent commit history",
    "tool_name": "git:log",
    "tool_args": {
        "limit": 5
    }
}
~~~

### Commit Message Guidelines

**Format**: `type: brief description`

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks
- `style:` - Code formatting

**Examples:**
- `feat: add user registration endpoint`
- `fix: resolve memory leak in file processing`
- `refactor: extract validation logic into separate module`
- `docs: update API documentation for authentication`
- `chore: update dependencies to latest versions`

### Critical Git Rules

1. **NEVER skip Git operations** - Every project must be version controlled
2. **Always commit after significant changes** - Don't accumulate too many changes
3. **Use meaningful commit messages** - Future developers need to understand what changed
4. **Check status regularly** - Know what changes are pending
5. **Initialize Git immediately** - Do this right after project creation
