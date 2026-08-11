# tool_policy.py DOX

## Purpose

- Own the single project/profile-aware tool policy used by catalogs, prompts, native
  schemas, local execution, MCP invocation, and delegated agents.

## Ownership

- `normalize_policy` owns the sparse allow/block configuration shape.
- `get_tool_catalog` owns canonical local, plugin, and MCP identities plus
  unavailable-policy retention; local entries come from executable `tools/*.py`
  files in the runtime path hierarchy. The catalog describes installed
  capabilities independently of transient transport availability; connector
  prompt/schema extensions remain responsible for live remote-tool exposure.
  The editor applies the current draft policy instead of receiving duplicated
  allowed/required flags from the backend.
- `tool_prompt_description` owns the shared compact description extracted for
  the editor catalog and provider-native schemas; transport-specific names and
  schemas remain with their transports.
- `resolve_tool` returns the effective decision and provenance.
- `ensure_tool_allowed` raises the stable repairable runtime policy error and
  accepts an explicit canonical ID from transports that already resolved one.
- `filter_tool_prompt` removes denied local capabilities from the text protocol,
  including complete fenced JSON examples that reference them, without taking
  ownership of provider-native naming rules.

## Runtime Contracts

- Scoped asset precedence comes from `helpers.plugins`: active project profile,
  active project, user profile, bundled/plugin profile, then default.
  `get_policy` selects the first custom policy; unknown-only and
  explicit-inherit files remain on disk but defer to the next lower layer.
- Missing policy inherits standard access. A custom policy records independent
  defaults for local/plugin tools and canonical MCP tools; explicit allowed or
  blocked IDs take precedence over either default.
- The `response` capability is a framework-required invariant: profile policy
  cannot disable it, and the editor does not list it as a configurable tool.
- `vision_load` remains owned by the active chat model's vision configuration;
  it is not exposed as a profile-policy choice and legacy policy IDs cannot
  suppress the chat-configured capability.
- Policy IDs are namespaced as `local:`, `plugin:<id>:`, or `mcp:<server>:`.
  Generic execution resolves canonical IDs from executable paths; MCP
  invocation supplies its explicit namespaced ID.
- Plugin IDs are derived relative to the canonical roots from `helpers.plugins`,
  not by independently parsing repository-relative path strings.
- Each executable local tool has its own policy identity, including tools that
  share one Markdown prompt.
- Catalog descriptions call the supplied agent's prompt loader instead of
  opening prompt files through a parallel path; the editor agent intentionally
  keeps its existing raw, no-processor implementation.
- Unknown policy IDs remain in the catalog as unavailable entries.
- Resolution performs no model calls and logs no secrets.

## Verification

- Run `tests/test_tool_policy.py` and the prompt/Responses/MCP focused tests.

## Child DOX Index

No child DOX files.
