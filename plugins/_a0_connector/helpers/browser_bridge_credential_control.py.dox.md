# Scoped credential controls

Own the production-only connector_bridge_credential_control dispatch. Exact v1
requests are rotate (rotation_id plus public_key), status (rotation_id), and
revoke (no further fields). Derive bridge, generation and subject from the exact
currently admitted principal. Never accept a caller-selected bridge or scopes.
Replies contain only contract_version, action, rotation_id, key_generation,
status and expires_at_ms. They contain no keys or credential material.

Self-revocation durably denies the record and pending generations, invalidates
outstanding challenges and withdraws route authority before network cleanup.
One retained task sends a bounded authenticated negative status and disconnects
only still-identical restricted sessions of that bridge/subject. Cancellation
cannot resurrect authority or cancel cleanup. Notification loss does not undo
revocation. No claimed or uncertain Chrome tab is closed by this controller.
