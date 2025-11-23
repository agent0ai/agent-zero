---
tags: [component, tools, python]
---

# Tools

Tools are capabilities that the [[Agent Core]] can invoke.

## Built-in Tools

- **Code Execution**: Handled by `CodeExecution` class. See [[Code Execution]].
- **Response**: `response_tool.py` - Sends final answer to user.
- **Browser**: `browser_use` integration for web interaction.
- **Memory**: `memory_tool.py` - explicit memory management.

## Structure

Tools are located in `python/tools/`.
They inherit from `python.helpers.tool.Tool`.

## Adding Tools

See [[Extensibility]] in main docs.

