---
name: new-tool
description: Scaffold a new agent tool for agent-zero. Creates the tool Python file in python/tools/ with correct boilerplate extending the Tool base class, and optionally scaffolds the prompt template and test file.
argument-hint: "<tool_name>"
---

# New Tool — Scaffold an agent-zero tool

Create a new tool named `$ARGUMENTS` (the tool name argument).

## Validation

- The tool name (`$ARGUMENTS`) must be a valid Python identifier in `snake_case` (lowercase, underscores, no hyphens or spaces). If it is not, suggest the corrected snake_case form and ask the user to confirm.
- Check that `python/tools/$ARGUMENTS.py` does not already exist. If it does, tell the user and abort.

## Step 1: Create the tool file

Create `python/tools/$ARGUMENTS.py` with this boilerplate:

```python
from python.helpers.tool import Response, Tool


class ClassName(Tool):
    """TODO: Describe what this tool does."""

    async def execute(self, **kwargs) -> Response:
        # TODO: Implement tool logic
        result = "Tool executed successfully."
        return Response(message=result, break_loop=False)
```

Where `ClassName` is the PascalCase version of `$ARGUMENTS` (e.g., `web_scraper` becomes `WebScraper`, `memory_export` becomes `MemoryExport`).

**Important conventions** (from examining existing tools):
- Import `Response` and `Tool` from `python.helpers.tool`
- The class extends `Tool`
- The main method is `async execute(self, **kwargs) -> Response`
- `execute` receives keyword arguments matching what the LLM passes as tool arguments
- Return a `Response(message=str, break_loop=bool)` — `break_loop=False` to continue the agent loop, `True` to end it
- Named parameters can be extracted from `**kwargs` as explicit keyword args (e.g., `async execute(self, query="", **kwargs)`)

## Step 2: Create the prompt template

Create `prompts/agent.system.tool.$ARGUMENTS.md` with a template describing the tool for the LLM:

```markdown
## Tool: $ARGUMENTS

TODO: Describe when and how the agent should use this tool.

**Arguments:**
- `arg_name` (string): Description of the argument.
```

Tell the user: "Edit the prompt template at `prompts/agent.system.tool.$ARGUMENTS.md` to describe the tool's purpose and arguments. This is what the LLM sees when deciding whether to use your tool."

## Step 3: Scaffold a test file

Create `tests/test_$ARGUMENTS.py` with this starter:

```python
"""Tests for the $ARGUMENTS tool."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestClassName:
    """Tests for the ClassName tool."""

    @pytest.mark.asyncio
    async def test_execute_returns_response(self):
        from python.tools.$ARGUMENTS import ClassName

        tool = ClassName(
            agent=MagicMock(),
            name="$ARGUMENTS",
            method=None,
            args={},
            message="",
            loop_data=None,
        )
        result = await tool.execute()
        assert result.message is not None
        assert result.break_loop is False
```

Where `ClassName` is the PascalCase version of `$ARGUMENTS`.

## Reminders

After creating the files, remind the user:

1. **Auto-discovery**: No registration is needed. The tool is auto-discovered by scanning `python/tools/`. Just having the file there makes it active.
2. **Prompt template**: Edit `prompts/agent.system.tool.$ARGUMENTS.md` to tell the LLM when and how to use this tool. The tool will not appear in the agent's system prompt until this template is properly written.
3. **Test**: Run the scaffolded test with `uv run pytest tests/test_$ARGUMENTS.py -v`.
4. **Conventions**: Use `snake_case` for function names, `PascalCase` for the class. Use `str | None` unions (not `Optional`).
