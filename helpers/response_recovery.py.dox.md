# response_recovery.py DOX

## Purpose and Ownership

- Own the shared consecutive unusable-response budget used by warning and repairable-exception hooks.
- `record_unusable_response(agent, limit)` returns a `HandledException` when the configured limit is reached; callers propagate it through their existing extension payload.

## Runtime Contracts

- Call only for classified unusable responses or `RepairableException`, not arbitrary warnings or critical/control-flow exceptions.
- Store only the last failed iteration and count under `_unusable_response_failures` in `LoopData.params_persistent`. This is per-monologue memory, not persisted settings or chat state.
- Count an iteration at most once across both callers, regardless of warning/error wording. Re-recording an exhausted iteration preserves the stop result without duplicating the log. A gap without a counted failure starts a new recovery window.
- Preserve the General Settings threshold: default 5; settings normalization clamps values to at least 1, not a disabled mode.
- At the threshold, log and return the existing core `fw.msg_unusable_response_limit.md` cost warning. Exception formatting/masking remains the repairable-exception hook's responsibility.
- Missing loop state is a no-op. There is no network, file, subprocess, or credential access.

## Verification

- `tests/test_repairable_response_limit.py` exercises real agent loop/tool/error dispatch offline, including repair, success, mixed failure, warning, and control-flow boundaries.
- `tests/test_unusable_response_loop.py` covers the original warning classification and configured threshold behavior.

## Child DOX Index

No child DOX files.
