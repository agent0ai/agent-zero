# System Prompt Extensions DOX

## Purpose

- Own construction of core system prompt sections.

## Ownership

- Ordered Python files own main, tools, MCP, secrets, skills, and project prompt sections.
- Active project instruction bodies and active-project AGENTS.md path-chain guidance are moved into prompt protocol; the system prompt keeps project metadata and stable project rules.

## Local Contracts

- Preserve ordering where sections depend on earlier context.
- Main, local-tool and MCP section owners register `LoopData.responses_prompt_replacements` while retaining normal text prompts. Responses applies these request-only substitutions when native A0 definitions are present; Chat and fallback keep the text protocol. MCP native framing preserves allowed-server context.
- Keep secret-related prompt sections masked and scoped.
- Prompt additions must be bounded and compatible with tool-call contracts.
- Keep non-tool sections free of configurable capability guidance; tool-owned
  guidance belongs in policy-filtered `agent.system.tool.*.md` prompts.
- Discover local tool prompts through `helpers.subagents.get_paths` and apply
  `helpers.tool_policy` before including their text.
- Omit the discoverable-skills catalog when profile policy blocks
  `skills_tool`; loaded skill history remains independent.

## Work Guidance

- Coordinate broad system prompt changes with profiles, skills, tools, plugins, and prompt tests.

## Verification

- Inspect rendered system prompts or run prompt-construction tests after changes.

## Child DOX Index

No child DOX files.
