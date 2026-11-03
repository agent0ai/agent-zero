# Tool Execute Before Extensions DOX

## Purpose

- Own backend processing immediately before tool execution.

## Ownership

- Ordered Python files own file-include expansion, prior tool-output replacement, parallel recursion guards, and secret unmasking before execution.

## Local Contracts

- Unmask only values required by the target tool.
- Preserve safety checks and do not expose secrets to logs or unrelated tools.
- Keep ordering stable where replacement must occur before unmasking or execution.
- `_05_replace_include_alias.py` expands `§§include(path)` recursively in argument values before tool-policy checks and secret unmasking. Mutate the original argument dictionary so both `tool.args` and execution kwargs receive file contents; unreadable files keep their placeholders through `helpers.strings.replace_file_includes`.
- Execution expansion must work without response streaming for Chat, native Responses calls, and parallel workers; the response-stream hook remains display-only.

## Work Guidance

- Coordinate with secret handling, tool argument preparation, and plugin tool gates.

## Verification

- Smoke-test tool execution with masked secret arguments and prior-output references after changes.
- Run `pytest tests/test_tool_file_includes.py tests/test_parallel_tool_args.py -q` for include expansion, hook ordering, and shared argument mutation.

## Child DOX Index

No child DOX files.
