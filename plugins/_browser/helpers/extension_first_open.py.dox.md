# First-open site authority

## Purpose and ownership

The installed production Browser service owns a separate process-only approval
before sending an `open` operation for an origin without existing permission.
This is not an extension challenge, native resolution control or native receipt.
The protected site inbox exposes its fixed `open` action class and origin only.

## Contract

- The caller first checks saved browsing policy. An explicitly enabled
  production All websites setting yields a generation-bound exact-origin
  grant, so no first-open request is created for that permitted origin.
  Neither pairing nor this helper enables the setting. Queued dispatch still
  rechecks the exact current policy grant, route and turn; disabling the setting
  withdraws its derived grants. Restricted URLs and consequential-action
  approvals remain independent. The rules below govern requests that were
  actually created because no saved permission existed.

- Retain at most 64 entries, a canonical HTTP(S) origin, opaque generated IDs,
  exact immutable operation binding and a server-owned current-binding check.
  Never retain full URLs, arguments or page content in these requests.
- Wait at most two minutes before broker dispatch. Only an explicit protected
  `deny`, `allow_once`, `allow_turn` or `allow_site` decision may settle the request. Validate
  subject, exact current principal object/SID/load/context/session/turn and
  selected bridge at decision, grant lookup and queued dispatch.
- `allow_once` initially permits only its original operation/action. After the
  real lease index accepts its correlated successful open result, permit site
  access only on that resulting exact owned handle in the same active turn.
  A second open, foreign lease or subsequent turn needs separate permission.
- `allow_turn` permits the same canonical origin for that exact route and live
  turn. Both choices expire within two hours, with no route or turn adoption.
  Existing per-action consequential consent remains independent.
- `allow_site` alone persists an exact-origin allow through the composed
  BrowserBridgePolicyRepository. Derive server instance from the owner and
  bridge/subject/origin from the retained request. Write and read back before
  releasing the waiter, then recheck current selection/turn and request expiry.
  A failed or uncertain save never releases the waiting operation. If authority
  disappears during a successful save, do not dispatch; the user's explicit
  saved-site choice may nevertheless remain and can be removed in settings.
  Normal saved-policy lookup owns later chat/turn access, rechecking the active
  bridge route and exact origin. Temporary request retirement never deletes an
  explicitly remembered policy. No wildcard, neighboring origin or native
  navigation `allow_site` choice is introduced.
- Request cancellation, expiry, route retirement, finalization and service
  uninstall withdraw pending state and wake waiters without browser dispatch.
  Stale bindings are pruned on every authority lookup. Unknown effects never
  create resulting-lease permission. Importing this helper installs nothing.
- The browser-host open handler independently enforces the server-origin grant
  and records the resulting owned lease. No wire schema or native grant-receipt
  rules are relaxed; cross-origin navigate keeps its existing native lane.

## Verification

Run the focused first-open, canonical runtime, site-authority and site-inbox
tests with synthetic routes/leases and an isolated framework runtime. Tests
must prove no send before choice/persistence, no saved policy write for temporary choices, exact once/turn scope,
stale/deny/expiry/cancel behavior and development-channel exclusion.
