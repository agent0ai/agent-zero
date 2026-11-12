# Production Browser runtime owner

`install_configured_browser_runtime` is reached from the enabled connector's
`webui_server_start` hook inside each ASGI lifespan, before serving requests, for
the `available` rollout and a configured production extension pin. It acquires
the real application/factory/lifecycle; missing release approval or transports
still prevents route admission. Shutdown and explicit reload await exact owner
retirement before replacement; constructors/imports do not install anything.
Successful installation registers awaited cleanup on that lifespan's
`shutdown` stack. Each startup retry installs afresh after prior cleanup, without
reconstructing the shared server or reusing a closed owner. Its manager check cannot
retire another server's replacement owner, and cleanup still runs if the plugin
is subsequently disabled. A separate Core create-end hook retains the read-only
legacy HTTP retirement guard even when the connector is disabled; it never
initiates retirement or grants activation. A disabled connector installs no
production runtime owner.
Production composition must acquire `get_extension_session_lifecycle()`, the
same KVP-backed singleton used by monologue hooks. A separately constructed
lifecycle misses those hooks and wrongly finalizes every Browser call as a
synthetic turn. Exact service-owner configuration/unconfiguration protects the
shared production singleton.

Admission rereads active paired credentials and explicit global-default or
current context selection. A saved global default permits handshake with no
loaded chats; context authorization still resolves that exact chat's effective
project/profile selection and preserves internal/other-host overrides. Admission
requires the same manager-owned principal/SID with authenticated traffic less
than 30 seconds old, and requires an absent legacy control plane. Native must
renew same-generation hello at most every 20 seconds; ordinary Engine.IO
connected state alone does not constitute this application heartbeat.
Read the exact connection activity and sample the comparison wall clock under
the same manager lock, in that order. An admission-start timestamp may precede
concurrent authenticated traffic and must not be used for that comparison.
Keep genuine future timestamps and ages of 30 seconds or more denied; never
clamp the age or broaden the freshness window to conceal a race.

The application reports genuinely composed runtime boundaries. An omitted
artifact or other required lane cannot be covered by a release approval or
client feature flag. The independently signature-verified release policy must
approve the exact extension/native tuple; its result is bound to the exact
principal/server/SID/load/install before constructing a fresh activation.

The new protected selection API may write production Browser configuration only
after active credential checks, then requires exact project-scoped or explicit
global-default readback.
Selection remains distinct from ready activation. No live-instance credentials,
release roots, policy file, rollout, or browser selection are generated here.

Production transport admission is provisional for browser operation/status
purposes until one exact reconciliation result promotes it. The first hello
emits no browser controls or finalization replay. The first same-principal/SID/
generation repeated hello proves the native transport consumed the initial ACK
and starts one process-owned reconciliation; no timing sleeps are used. Its
hello projection is unchanged, so native renewal equality remains exact.
Replacement resets reconciliation; timeout/mismatch retires the exact route.
Context, artifact, approval and operation authority remain denied until
promotion. Reconciliation validates peer inventory but adopts no lease authority.

Private stage diagnostics distinguish initial admission, renewal, reconciliation
start/result/success and a fixed allowlist of failures. Settled negative replies
may classify invalid state, unsupported capability, internal error or unknown
outcome without exposing remote error text. Unknown codes map to OTHER_FAILURE;
each symbol is logged at most five times per process, so an absent recent log
does not prove that no retry occurred. Diagnostic symbols never grant readiness.
Admission rejection symbols identify only the failed predicate: owner, socket,
principal, extension pin, rollout, selection, heartbeat, legacy isolation,
required boundaries, release proof or its exact binding. Exceptions report
only `ADMISSION_CHECK_EXCEPTION`, never values or exception text. Checks retain
their original order and all remain required.

Verify with `tests/test_browser_bridge_runtime_owner.py` and runtime registry tests.
