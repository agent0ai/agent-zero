# responses_tools.py DOX

## Purpose

- Own conversion of Agent Zero tool prompt files and MCP tool metadata into OpenAI Responses API function tool definitions.
- Keep native Responses function availability synchronized with the text tool prompt surface.

## Ownership

- `responses_tools.py` owns runtime implementation.
- `responses_tools.py.dox.md` owns durable notes about responsibilities, prompt-derived contracts, and verification for this helper.

## Local Contracts

- Build local function tools from enabled `agent.system.tool.*.md` prompt files and include `vision_load` when either Main native vision or the effective preset's Vision Model enables the canonical vision prompt.
- Discover local prompt files through `helpers.subagents.get_paths`; this module
  owns the Responses-specific prompt-name compatibility rules.
- Local prompt-derived function names use existing bullet declarations that pair a backticked name with `arg` or `args` for multi-tool prompt files, otherwise prefer explicit `"tool_name"` examples, then the first prompt heading, and finally the prompt filename.
- Apply registered tool-prompt render kwargs before deriving native metadata so descriptions never expose unresolved prompt templates.
- Emit generated definitions with `strict: false` so Responses does not normalize optional or extensible arguments into required strict fields. Provider-specific strictness (such as Codex's final response) belongs at the provider request boundary.
- Explicitly embedded JSON schemas take precedence. Otherwise use canonical argument properties only for a matching resolved bundled implementation in `BUNDLED_TOOL_PARAMETERS`; custom/profile overrides must not inherit a same-named bundled contract. Properties remain optional and extensible for action-dependent inputs and runtime aliases; runtime validation remains authoritative.
- For unlisted implementations, infer only an unambiguous single backticked argument on an otherwise empty `args:` line; otherwise retain a permissive object instead of prose-guessed types.
- Native local descriptions preserve full policy-filtered operational guidance. Convert unfenced and JSON-fenced A0 envelope examples to argument-only examples using the shared tool-request parser; preserve unrelated JSON and non-JSON code fences. Catalog summaries remain separate.
- Preserve original Agent Zero tool names through the native Responses name map.
- Keep MCP tool schemas merged after local prompt-derived tools.
- Apply `helpers.tool_policy` before emitting local or MCP schemas; a blocked
  capability is absent from provider-native tool definitions. Vision routing
  is controlled by the effective model preset rather than Agent Editor.
- Resolve a fresh policy once per schema build and reuse it only within that
  build; runtime execution remains independently policy-gated.
- Connector remote tools are advertised only when `_a0_connector` runtime metadata says the matching connected CLI capability is currently available.

## Work Guidance

- Do not silently truncate local or MCP instructions; prompt owners control their guidance budget.
- Treat plugin-specific tool gates as optional imports so core helper loading does not require a plugin that is absent or disabled.

## Verification

- Run targeted Responses/tool prompt tests after changing function-tool construction.
- Run connector prompt gating tests when changing remote tool availability.
