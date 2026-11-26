# Team run coordination

## Ownership

- The coordinator reserves work against `TeamStore` and binds the resulting run to native `AgentContext.communicate` and `run_task` hooks.
- `request_stop()` records the stop before scheduling cancellation on the actual coroutine. A stop that arrives before launch is observed when the coroutine starts.
- `recover_on_startup()` claims a process-lifetime lock on the team data volume and retires reservations left by an exited framework process.

## Contracts

- The database owns the active run, request fingerprint, and terminal outcome. The process-local task map only locates the coroutine to cancel.
- Every native team turn enters with a matching reservation. The coroutine saves native context state and finalizes its own run ID during teardown.
- `executing_scope()` revalidates the active run and its actor’s current project access before project tool operations.
- Team queue actions require the exact active hold and the holder's current grant. The existing native queue APIs delegate here. Messages run FIFO after the current turn, or at a native intervention checkpoint when explicitly promoted. The holder alone sees pending queue text. Stop, revocation, and process restart discontinue pending work.
- The response-only runtime has no independently surviving tool workers. An isolated tool runner must report its own exit before a future integration can release a reservation.

## Verification

- Check competing sends from two members, concurrent chats, duplicate request IDs, cancellation before launch, cancellation during a turn, and recovery after terminating the QA process.
- Project compaction uses the same occupancy reservation as message turns, with a maintenance kind that closes the message queue.
