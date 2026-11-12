# Browser bridge queue controller

## Ownership

- Own strict `connector_message_queue_add`, `remove`, and `send` dispatch.
- Reuse the Core `helpers.message_queue` for AgentContext queue storage, and
  the bridge message dispatcher for once-only explicit text delivery.

## Inputs and effects

- All requests require integer `contract_version: 1` and `context_id`.
- Add additionally requires `client_message_id` and nonblank UTF-8 `text`
  bounded to 32 KiB. Remove and send require one exact `item_id` returned by
  add. Batch/global clears, paths, attachments, caller subjects and raw route
  bindings are not accepted by this lane.
- Recheck current immutable principal/SID/load and advertise-before-message
  access before every effect. Only queue items created by the same server,
  bridge, subject and context are visible or actionable; foreign Core queue
  entries remain untouched and are not projected.
- The normal Core queue consumer may consume an accepted item independently
  of presentation. An old add never recreates an item once accepted.
- Persist hash-only reservations before effects and final states afterwards.
  Duplicate content conflicts; uncertain effects are never automatically
  repeated. Explicit send removes the queue entry before model/log delivery
  and retains an uncertain tombstone on failure. Hash receipts use the shared
  plugin journal's individually indexed atomic KVP records; historical v1
  receipts remain a read-only fallback and are never evicted. A schema-v2 marker
  is persisted before the first indexed write so older builds fail closed on
  downgrade. Lifetime usage
  does not exhaust a fixed record quota; disk use grows with distinct IDs.
  The Core queue remains bounded to 32 entries for this producer.
- Responses contain version, context, opaque item ID, status and at most 32
  owned previews of 100 characters, never attachment references. Send the
  same bounded queue projection through exact-principal restricted emission.
  A failed presentation after an effect reports unknown, not not-applied.
- The existing subscribed-context poller calls `project` on subscribe and on
  its normal tick, sending only changed owned projections. Reopening a panel
  restores current queue state and ordinary Core consumption clears its item;
  no second polling task or reconnect resend is created.

## Verification

- `tests/test_browser_bridge_queue.py` exercises the real Core queue with a
  synthetic context, durable in-memory stores and no model/network effects.
- Full native codecs, runtime admission, release trust and publication are
  separate; this helper does not assert readiness.
