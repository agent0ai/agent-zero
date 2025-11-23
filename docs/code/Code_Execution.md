---
tags: [component, execution, security]
---

# Code Execution

The `CodeExecution` tool (`python/tools/code_execution_tool.py`) allows the agent to run code.

## Runtimes

- **Python**: Executed via `ipython`.
- **NodeJS**: Executed via `node`.
- **Terminal**: Shell commands (Bash/PowerShell).

## Environment

Code runs in:
- **Docker**: Default, safe environment.
- **Local**: Optional, runs on host (risky).
- **SSH**: Remote execution.

## Relations

- Called by [[Agent Core]].
- Uses [[Helpers]] for shell management (`shell_local`, `shell_ssh`, `docker`).

