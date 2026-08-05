# responses_tools.py DOX

## Purpose

- Own conversion of Agent Zero tool prompt files and MCP tool metadata into OpenAI Responses API function tool definitions.
- Keep native Responses function availability synchronized with the text tool prompt surface.

## Ownership

- `responses_tools.py` owns runtime implementation.
- `responses_tools.py.dox.md` owns durable notes about responsibilities, prompt-derived contracts, and verification for this helper.

## Local Contracts

- Build local function tools from enabled `agent.system.tool.*.md` prompt files and include `vision_load` only when the active chat model enables the matching vision prompt.
- Discover local prompt files through `helpers.subagents.get_paths`; this module
  owns the Responses-specific prompt-name compatibility rules.
- Local prompt-derived function names use existing bullet declarations that pair a backticked name with `arg` or `args` for multi-tool prompt files, otherwise prefer explicit `"tool_name"` examples, then the first prompt heading, and finally the prompt filename.
- Apply registered tool-prompt render kwargs before deriving native metadata so descriptions never expose unresolved prompt templates.
- Use an explicitly embedded JSON input schema when present. Infer only an unambiguous single backticked argument on an otherwise empty `args:` line; all other local tools receive an honest permissive object schema instead of prose-guessed types.
- Native local-tool descriptions reuse the tool catalog's compact prompt
  description; Responses retains native-name mapping, schema derivation, and
  provider description limits.
- Preserve original Agent Zero tool names through the native Responses name map.
- Keep MCP tool schemas merged after local prompt-derived tools.
- Apply `helpers.tool_policy` before emitting local or MCP schemas; a blocked
  capability is absent from provider-native tool definitions. Vision remains
  controlled solely by the active chat model configuration.
- Connector remote tools are advertised only when `_a0_connector` runtime metadata says the matching connected CLI capability is currently available.

## Work Guidance

- Keep prompt-derived descriptions bounded by `MAX_TOOL_DESCRIPTION_CHARS`.
- Treat plugin-specific tool gates as optional imports so core helper loading does not require a plugin that is absent or disabled.

## Verification

- Run targeted Responses/tool prompt tests after changing function-tool construction.
- Run connector prompt gating tests when changing remote tool availability.
