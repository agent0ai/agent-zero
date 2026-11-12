# Browser credential rotation

The pairing repository and its existing RLock own every read-modify-write.
Persist only one optional strict public-key rotation record beside the active
credential. Requests cannot change subject, extension, bridge, installation or
scopes. Ten-minute pending generations never replace the active key until a
fresh one-use challenge has verified the exact new public key. Authentication
tries at most the active and live pending key; the verified-key commit compares
public key, rotation ID, generation and immutable identity under the same lock,
preventing pending-generation ABA. Failed proofs, expiry or persistence retain
the previous key. A successful commit invalidates old-key admission immediately;
old work may end uncertain and is never replayed. Revocation clears pending keys.
Only public records survive restart. This helper never generates private keys.

Existing version-1 records without rotation remain readable. Generations are
strict positive bounded integers, not booleans. Unknown optional fields fail.
The extension/native companion still needs its own interruption-safe private-key
staging and new authenticated session before local old-key deletion.

Verification: tests/test_browser_bridge_credentials.py uses actual Ed25519
signatures with synthetic records and clock; no live credentials or model calls.
