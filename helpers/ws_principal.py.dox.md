# Restricted WebSocket principal

`WsPrincipal` is an immutable, server-derived identity and allowlist for a
non-session WebSocket client. Collections are copied into frozensets. It holds
no proof, nonce, signature, cookie, API key, or private key. The authenticating
handler owns scope-to-event mapping and ongoing credential validation.

Both event name and authenticated handler identity must match. Restricted
clients never join ordinary user fan-out, global handler lifecycle/dispatch,
diagnostic watchers, or reconnect buffers. `restricted_correlation_id` bounds
client correlation metadata; bridge diagnostics must not retain even permitted
correlation values or primitive payloads. Legacy clients use no principal and
retain their existing authentication and event behavior.

Verify with `tests/test_ws_restricted_principal.py` plus WebSocket regressions.
