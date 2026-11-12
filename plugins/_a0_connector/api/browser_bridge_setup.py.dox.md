# Browser setup WebUI API

`POST /api/plugins/_a0_connector/browser_bridge_setup` accepts an empty JSON object only under the normal session authentication and CSRF protection. Use `ApiHandler`, not the connector API-key/loopback override handler. Reject nonempty/malformed bodies, including bodies hidden by generic API parsing, through the existing bounded metadata request validator.

Return only the helper's `a0.browser-bridge.setup.v1` public projection with `Cache-Control: no-store`. This endpoint reads configured release links; it never fetches or verifies catalog/artifact bytes, changes settings, enables browser control, installs inside Docker, or accepts caller-selected URLs. See the helper sidecar for fail-closed gate, per-OS and host-verification semantics.
