# browser_bridge_selection.py DOX

## Purpose

- Resolve the extension bridge selected for one live Agent Zero context without
  treating a WebUI Browser ID or request value as authority.

## Local Contracts

- Load the exact `AgentContext`, require its own `agent0`, and read that agent's
  project/profile `_browser` configuration through `get_browser_config`.
- Return a bridge only when `runtime_backend` is exactly `host_required` and
  `host_browser_selection` is a valid `extension:<bridge_id>` selection.
- Fail closed on missing contexts, malformed configuration, invalid identifiers,
  import/load failures, or agent/context mismatch.
- Callers must recheck `selection_current(context_id, bridge_id)` at challenge
  registration, decision, and queued-control authorization boundaries.

## Non-Goals

- Read-only selection resolution does not resolve container Browser tab IDs,
  choose a bridge, test route liveness, or grant runtime/operation authority.

## Protected selection mutation

`select_bridge_for_context` is the protected API's explicit mutation path. It
requires the real current context, active server/subject paired record, pinned
extension and installed available production owner. Writes hold a lexical
config capability unavailable to generic settings requests, target Browser's
project scope with empty agent profile, and must pass exact readback. The former
bridge route is retired first; failure cannot route old operations to a new
browser. Clearing remains possible without an available owner. This helper does
not grant readiness: hello must independently pass release/runtime admission.

`select_default_bridge` is an explicit global-only mutation with an exact
previous-bridge precondition, including null for the first default. It loads and
writes only global Browser config (empty project/profile), preserves its other
settings, checks active pairing before and after persistence, and retires the
former route before replacement. Clearing remains available without a runtime
owner. Existing project/profile configuration is never rewritten or merged;
framework whole-file precedence preserves those overrides. `default_selected_bridge`
reads this default without a loaded chat and supplies selection evidence only,
not credential validity or context/action authority.
