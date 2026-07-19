# Tool Execute Before Extensions DOX

## Purpose

- Own backend processing immediately before tool execution.

## Ownership

- Ordered Python files own prior tool-output replacement, parallel recursion guards, and secret unmasking before execution.

## Local Contracts

- Unmask only values required by the target tool.
- Preserve safety checks and do not expose secrets to logs or unrelated tools.
- Keep ordering stable where replacement must occur before unmasking or execution.

## Work Guidance

- Coordinate with secret handling, tool argument preparation, and plugin tool gates.

## Verification

- Smoke-test tool execution with masked secret arguments and prior-output references after changes.

## Child DOX Index

No child DOX files.
