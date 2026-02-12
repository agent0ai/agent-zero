---
name: new-api
description: Scaffold a new API endpoint for agent-zero. Creates the handler Python file in python/api/ with correct boilerplate extending the ApiHandler base class, and optionally scaffolds a test file.
argument-hint: "<endpoint_name>"
---

# New API Endpoint — Scaffold an agent-zero API handler

Create a new API endpoint named `$ARGUMENTS` (the endpoint name argument).

## Validation

- The endpoint name (`$ARGUMENTS`) must be a valid Python identifier in `snake_case` (lowercase, underscores, no hyphens or spaces). If it is not, suggest the corrected snake_case form and ask the user to confirm.
- Check that `python/api/$ARGUMENTS.py` does not already exist. If it does, tell the user and abort.

## Step 1: Create the API handler file

Create `python/api/$ARGUMENTS.py` with this boilerplate:

```python
from python.helpers.api import ApiHandler, Input, Output, Request


class ClassName(ApiHandler):
    """TODO: Describe what this endpoint does."""

    async def process(self, input: Input, request: Request) -> Output:
        # TODO: Implement endpoint logic
        return {"status": "ok"}
```

Where `ClassName` is the PascalCase version of `$ARGUMENTS` (e.g., `user_settings` becomes `UserSettings`, `export_data` becomes `ExportData`).

**Important conventions** (from examining existing handlers):
- Import `ApiHandler`, `Input`, `Output`, and `Request` from `python.helpers.api`
- The class extends `ApiHandler`
- The main method is `async process(self, input: Input, request: Request) -> Output`
- `input` is a `dict` parsed from the request JSON body
- Return a `dict` (serialized as JSON 200) or a Flask `Response` object
- The endpoint URL is auto-derived from the filename: `python/api/user_settings.py` becomes `/user_settings`

### Optional overrides

If the endpoint needs non-default behavior, the user should override these class methods as needed:

```python
@classmethod
def requires_auth(cls) -> bool:
    return True  # Default. Set False for public endpoints.

@classmethod
def requires_csrf(cls) -> bool:
    return True  # Default (follows requires_auth). Set False if needed.

@classmethod
def get_methods(cls) -> list[str]:
    return ["POST"]  # Default. Use ["GET"] or ["GET", "POST"] as needed.
```

Include these overrides in the generated file only if the user specifies non-default values. Otherwise, omit them so the defaults from `ApiHandler` apply.

## Step 2: Scaffold a test file

Create `tests/test_$ARGUMENTS.py` with this starter:

```python
"""Tests for the $ARGUMENTS API endpoint."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestClassName:
    """Tests for the ClassName API handler."""

    @pytest.mark.asyncio
    async def test_process_returns_dict(self):
        from python.api.$ARGUMENTS import ClassName

        handler = ClassName(app=MagicMock(), thread_lock=MagicMock())
        result = await handler.process({}, MagicMock())
        assert isinstance(result, dict)

    def test_requires_auth(self):
        from python.api.$ARGUMENTS import ClassName

        # Adjust if your endpoint should be public
        assert ClassName.requires_auth() is True

    def test_default_methods(self):
        from python.api.$ARGUMENTS import ClassName

        assert "POST" in ClassName.get_methods()
```

Where `ClassName` is the PascalCase version of `$ARGUMENTS`.

## Reminders

After creating the files, remind the user:

1. **Auto-discovery**: No registration is needed. The handler is auto-discovered by scanning `python/api/`. The endpoint URL is derived from the filename (underscores become the URL path, e.g., `user_settings.py` serves `/user_settings`).
2. **Authentication**: By default, endpoints require auth and CSRF. Override `requires_auth()` and `requires_csrf()` to change this.
3. **HTTP methods**: By default, only POST is allowed. Override `get_methods()` to add GET or other methods.
4. **Context access**: Use `self.use_context(ctxid)` to get an `AgentContext` if the endpoint needs to interact with an agent instance.
5. **Test**: Run the scaffolded test with `uv run pytest tests/test_$ARGUMENTS.py -v`.
6. **Conventions**: Use `snake_case` for function names, `PascalCase` for the class. Use `str | None` unions (not `Optional`).
