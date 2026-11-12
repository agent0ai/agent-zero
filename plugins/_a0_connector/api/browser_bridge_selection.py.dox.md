# Production Browser selection API

Normal ApiHandler authentication and CSRF remain mandatory. Strict bounded
duplicate-key-rejecting JSON accepts `status`, `use`, `clear` with context ID;
`use` additionally takes a paired bridge ID; `clear` requires `expected_bridge_id`
checked under the mutation lock before any retirement/write. No server identity, subject,
credential, policy, or readiness is accepted from the request.
Non-string actions return HTTP 400 before default or context dispatch.

`use` requires the installed production owner, available rollout, current
server/subject active pairing and pinned extension. The helper writes only
Browser's real project scope and checks exact readback. Changing or clearing
selection retires the prior bridge route before configuration effects.

No-store status is ready only from exact current admitted route resolution;
selection alone returns reconnect-required, never ready.

Global actions have no context prerequisite: `default_status` accepts only
action; `use_default` requires bridge_id and nullable expected_bridge_id;
`clear_default` requires nonnull expected_bridge_id. Both writes compare the
exact previous global default under the helper lock. They preserve every scoped
override. The strict `a0.browser-bridge.default-selection.v1` response has only
contract, bridge_id, selected, browser_control_ready, reconnect_required.
Readiness is a boolean-only current admitted bridge lookup, not context or
operation authorization. Invalid shapes return 400; unavailable or stale
mutations return 409 with the existing bounded error. All responses are no-store.
