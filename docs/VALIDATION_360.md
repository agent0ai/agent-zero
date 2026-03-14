# Validation 360

Purpose: run one repeatable gate that checks runtime health, chat orchestration, skills discovery, and core integration tests.

## Command

```bash
./scripts/validate_360.sh
```

Optional full mode:

```bash
./scripts/validate_360.sh full
```

## What it validates

1. Core compile checks for routing/runtime modules.
2. Tool constructor compatibility contract (prevents `Tool.__init__` signature regressions).
3. MCP cache/reload tests.
4. Project lifecycle and validation tests.
5. Context persistence compatibility after restart:

- `tests/test_telegram_bridge_restart_persistence.py`
- validates persisted `chat_id -> ctxid` mapping survives module reload (restart simulation)
- validates legacy state file without `last_update` remains readable and dedupe state is persisted after reload

6. Live API checks:

- `/health`
- `/chat_readiness`
- chat roundtrip (`/chat_create` -> `/message_async` -> `/poll`)
- `/skills_list` discovery

7. Full mode adds heavier integration subset.

## Output

- Writes timestamped report to `artifacts/validation/validation-360-<timestamp>.log`.
- Exit code `0` only when all checks pass.

## Success criteria

- No failed checks in summary.
- Each check prints `[PASS] <name>` in the report; any `[FAIL]` causes non-zero exit.
- Context persistence check passes only if persisted mappings remain intact across reload and legacy state remains compatible.
- Chat roundtrip settles (poll reaches non-active progress with accumulated logs).
- Skills discovery returns at least one registered skill.
- Constructor contract test passes for all tools.
