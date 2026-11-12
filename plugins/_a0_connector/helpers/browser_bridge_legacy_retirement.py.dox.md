# Explicit legacy retirement

`LegacyRetirement` is an opt-in local retirement adapter, not a bridge-v1
activation or migration-readiness authority. Normal startup only installs the
Flask request guard; no journal means no retirement effects. A corrupt or
interrupted journal blocks only legacy Chrome bridge requests/tools, never
unrelated WebUI APIs. Both the canonical `/api/plugins/chrome_extension/`
routes and defensive `/plugins/chrome_extension/` alias are covered. Existing
in-flight legacy requests prevent starting retirement.

The authenticated, CSRF-protected retirement endpoint requires explicit
confirmation covering all legacy plugin scopes. It accepts only an inspected,
structurally confirmed prototype root and, if loaded, the exact bounded source
digest and known process-registry shape. It never imports an unloaded legacy
plugin to create proof. Ambiguous roots, multiple registries, unsafe filesystem
inspection, malformed commands, or storage failures fail closed.

Under the original registry lock, producers and redelivery stop before queued
commands become `CANCELED_NOT_APPLIED`. Only already-dispatched exact
session/command receipts may complete once, until the earlier original deadline
or thirty seconds. Unresolved commands become `OUTCOME_UNKNOWN` and are never
replayed. Incoming payloads, screenshots and tab metadata are discarded. The
process registry is scrubbed before the existing global plugin toggle disables
the prototype and clears its scope overrides. No token rotation, old-authority
transfer, browser automation, tab closure, plugin-file deletion, or v1 selection
occurs. The persisted journal contains only a migration UUID, timestamps, state
and bounded counters. An interrupted journal never silently resumes.

The `Agent.get_tool` extension rejects only `chrome_bridge` after retirement
begins. `browser_bridge_legacy_quarantine.py` owns the recoverable, exact-owner
context/history lazy persistence hooks and bounded loaded-context sweep.
Browser-local storage cleanup, cross-extension-ID cleanup attestation, dormant
chat loading, and full production cutover remain separate requirements.
Status therefore always reports `activation_ready: false` and
operator-required local browser cleanup. The read-only cutover detector and
runtime owner's existing legacy admission checks are not bypassed.

Focused tests use an exact, inert prototype source fixture and temporary
registries. They must not touch live plugin credentials, contexts, or browser
tabs.
