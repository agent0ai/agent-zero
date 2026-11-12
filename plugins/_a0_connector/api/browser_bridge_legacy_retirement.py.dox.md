# Legacy retirement API

Normal `ApiHandler` session authentication and CSRF checks are mandatory; this
is not an API-key or extension-facing endpoint. Strict bounded unique-key JSON
accepts exactly `{ "action": "status" }` or
`{ "action": "retire", "confirmed_all_legacy_scopes": true }`.
It also accepts exactly `{ "action": "quarantine",
"confirmed_all_legacy_scopes": true, "offset": 0 }` for a bounded page of
currently loaded contexts after retirement began. The offset is an integer
from zero through 10,000, not a caller-supplied context/path. Quarantine replies
contain safe counts and the next offset only; read the quarantine helper DOX
for recoverability, lazy dormant-chat handling and scope limits.

Status is read-only and redacted. Retirement explicitly stops all scopes of the
confirmed prototype through `browser_bridge_legacy_retirement`; it never
selects or activates bridge v1. The response is no-store; malformed input is
400, blocked/incomplete retirement is 409, completed legacy disabling is 200.
Never expose underlying exceptions, paths, legacy credentials or payloads.
