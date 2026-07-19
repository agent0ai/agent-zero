# responses_tools.py DOX

## Purpose

- Own conversion of Agent Zero tool prompt files and MCP tool metadata into OpenAI Responses API function tool definitions.
- Keep native Responses function availability synchronized with the text tool prompt surface.

## Ownership

- `responses_tools.py` owns runtime implementation.
- `responses_tools.py.dox.md` owns durable notes about responsibilities, prompt-derived contracts, and verification for this helper.

## Local Contracts

- Build local function tools from enabled `agent.system.tool.*.md` prompt files.
- Local prompt-derived function names prefer explicit `"tool_name"` examples, then the first prompt heading, and only fall back to the prompt filename when the prompt declares no callable name.
- Function parameter schemas are object schemas with an explicit `properties` object so OpenAI-compatible servers that validate chat-style tool payloads accept permissive tools.
- Preserve original Agent Zero tool names through the native Responses name map.
- Keep MCP tool schemas merged after local prompt-derived tools.
- Connector remote tools are advertised only when `_a0_connector` runtime metadata says the matching connected CLI capability is currently available.

## Work Guidance

- Keep prompt-derived descriptions bounded by `MAX_TOOL_DESCRIPTION_CHARS`.
- Treat plugin-specific tool gates as optional imports so core helper loading does not require a plugin that is absent or disabled.

## Verification

- Run targeted Responses/tool prompt tests after changing function-tool construction.
- Run connector prompt gating tests when changing remote tool availability.
