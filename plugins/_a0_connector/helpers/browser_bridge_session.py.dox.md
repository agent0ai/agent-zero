# Browser bridge scoped-session foundation

`authenticate` verifies the exact singleton-handler proof envelope after shared
Origin checks, rechecks the current server URL/instance and pinned extension,
and returns a server-derived `WsPrincipal`. `is_active` rechecks rollout,
credential state, subject, extension, key generation and scopes on requests.
The namespace supplies neither ambient cookies nor API/CSRF tokens.

Without an explicitly installed server-owned Browser bridge application, only
`connector_hello` is accepted. Its input is not stored or interpreted as CLI
remote-tool metadata, and the response contains no runtime features and reports
session/browser runtime readiness false. Installing the optional application
freezes the full bridge-only event allowlists into newly authenticated
principals. Exact hello admission then returns only negotiated metadata, typed
activation evidence, and the authenticated transport binding. All operational
events dispatch exclusively to that application and never to legacy connector
branches; a missing application or unadmitted SID fails closed. Existing
hello-only principals must reconnect and prove again before they can acquire
the larger immutable event sets.

The transport-only connector binding may include server instance, bridge, SID,
key generation, and load generation inside the already proof-authenticated
Socket.IO acknowledgement. Never reuse those values in Browser status/WebUI.
Normal WebUI startup composes the production owner only with available rollout
and a production extension pin; the admission evaluator independently verifies
signed release approval, complete boundaries, exact selection and fresh activity.
Removing an installed owner requires the
bootstrap's async retirement path, which hides it from new routing, awaits its
route/controller cleanup, and only then clears the site-authority API binding.

No persistence except the existing proof verifier's last-authenticated update.
Verify with restricted WebSocket, Browser bridge session, and optional
bootstrap handler regression tests.
