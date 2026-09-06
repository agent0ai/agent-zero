# Browser bridge transport profiles DOX

## Purpose

- Own the fixed production Browser bridge transport identity.
- Separate principal/handler routing identity from runtime admission and from
  each controller's lane-specific scope and event checks.

## Local Contracts

- Accept only the exact module-owned production profile
  object. Protocol fields, environment strings, configuration values and
  caller-constructed lookalikes never select a transport.
- Validate that single identity directly; there is no profile registry or
  alternate-channel search. Identity-only validation still grants no scopes.
- Production uses `browser_bridge`, `plugins/_a0_connector/ws_connector` and
  `ws_connector.WsConnector`, on `/ws`. Retired development identities and
  caller-created lookalikes are rejected, even with full production scopes.
- Structural helpers may recognize a fixed principal/handler identity while
  preserving their existing lane-specific scope and event checks. Only the
  runtime registry requires the complete immutable runtime sets.
- Transport identity grants no readiness, capability, route, persistence or
  Browser authority. Complete runtime admission and activation serialization
  remain production-only.
- Composed emitters use the selected profile's handler ID and namespace and
  recheck exact profile identity at controller, settlement and route seams.
  Production is the compatibility default.
## Verification

- Run `pytest tests/test_browser_bridge_transport_profiles.py` plus the
  directly affected Browser bridge runtime/controller/authority groups.

## Child DOX Index

No child DOX files.
