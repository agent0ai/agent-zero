# Production browser selection view

Owns the replaceable Browser Settings projection of the protected
`browser_bridge_selection` API. An explicit Use this Chrome browser button sets
the global default through the exact v1 default-selection contract, including
when no chat exists. Clearing is confirmed. Reads never select or pair.

Exact response keys, contract, context (for the separate chat projection) and bridge are checked. Every async result
is fenced by mount generation and current chat. Readiness comes only from the
protected response, not inventory, pairing or a local setting. Only authoritative
settings readback for the modal's own scope updates its routing draft, preserving
Global versus project separation. Cleanup removes only presentation state.

Default writes include `expected_bridge_id` from the last successful default
readback (null only for use with no prior default); unavailable status disables
new writes. Existing explicit project/profile choices remain unchanged and the
current-chat projection explains any different selection without claiming the
default failed. No context ID is sent to the three default actions. Default
readiness is server-derived, never inferred from the current chat or pairing.

The selection store owns a five-second read-only readiness refresh while mounted
and the document is visible, independently of the Browser config coordinator's
inventory refresh. Its injected timer is stopped on cleanup; mount generation,
current chat, loading and mutation-busy guards prevent stale or overlapping
checks. Late initial refresh cannot create a timer after cleanup. A quiet in-flight check preserves the previous
status label; an actual failure clears readiness. No timer can select a browser,
move a settings modal to a different chat, or imply readiness from saved pairing.
