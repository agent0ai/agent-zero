# Recoverable legacy context/history quarantine

This plugin-owned migration runs only after a valid explicit retirement journal
exists. A missing or corrupt journal grants no mutation permission. It never
maps old keys or identifiers to browser-v1 authority.

The generic `persist_chat._serialize_context` and `_deserialize_context`
extension seams invoke the plugin's synchronous start hooks. Save/export
quarantines live main/subordinate histories before serialization; load/import
quarantines the serialized document before context creation. Only the exact
`source == "chrome_extension"` context removes `source`,
`chrome_browser_session_id`, and `chrome_extension_capabilities`.

History traversal follows only actual History/Bulk/Topic/Message structural
edges. Only non-AI Message content with exact `tool_name: chrome_bridge`, string
tool result/session/command IDs and a terminal command status loses its
`image_data_url` member. Exact JSON tool-result summaries on the same owned
Message receive the same treatment; prose, unknown structures, user messages,
metadata, explicit attachments, safe outcome fields and dimensions stay intact.
Token caches of changed live messages are invalidated. Repeated runs are no-ops.

Before removing anything, retain only removed values and structural locations
in a content-addressed recovery blob under
`usr/browser_bridge_legacy_quarantine`. It is outside normal chat loading and
artifact transport, never returned by the API and never automatically restored.
The root/usr/quarantine chain is opened with descriptor-relative no-follow
checks; the quarantine directory is owner-only 0700 and new blobs 0600. Files
are exclusive-create, flushed and fsynced before mutations. Existing blobs must
match exact bytes, owner, private mode and single-link regular-file shape. No
overwrite or automatic purge occurs. An interrupted partial blob fails closed
for manual operator repair. Recoverability does not authorize re-enabling old
credentials or browser bindings; any recovery is an explicit operator action.

Bound the recovery object to 32 MiB, 1,024 removed members, 10,000 structural
records and 64 agents/nesting components. Storage failure, concurrent slot
changes, ambiguous candidate JSON or exceeded limits abort before mutation.
Repeated live references to the same dictionary/key are rejected before any
backup or removal so aliasing cannot produce a partially applied deletion.
Private backup data is deliberately separate from the redacted retirement
journal. Do not log it or include it in v1 inventories.

The authenticated, CSRF-protected `quarantine` API action additionally requires
explicit all-legacy-scopes confirmation and an integer offset. It processes at
most 20 currently loaded contexts per request using normal atomic chat saves.
Offsets refer to the current sorted inventory, not a durable snapshot; repeat
from zero if contexts change. Dormant saved chats are not read or overwritten
by the sweep and are migrated on their next normal load. The response labels
that scope and always reports `activation_ready: false`; no whole-installation
cleanup claim is made. Chrome storage in an old extension ID/profile and its
tabs are outside Core authority and remain operator-owned cleanup.

Verification uses synthetic histories/private temporary roots and the actual
decorated persistence path; never run tests against live chats or quarantine.
