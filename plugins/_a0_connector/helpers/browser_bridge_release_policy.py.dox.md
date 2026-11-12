# Signed server Browser release policy

Reads only the absolute operator-configured `A0_BROWSER_BRIDGE_RELEASE_POLICY_FILE`
as a bounded no-follow regular file. It never downloads code or reads native
credentials. Requests and extension metadata cannot choose its path or keys.

Envelope keys are exactly `key_id`, `policy`, `signature`; signature is canonical
standard-base64 Ed25519 over sorted compact UTF-8 JSON of `policy`. Duplicate
keys at every depth are denied. Policy keys are exactly `contract`,
`issued_at_ms`, `expires_at_ms`, `releases`. Contract is
`a0.browser-bridge.server-release-policy.v1`; issue/expiry are safe integers,
valid at verification and at most 90 days apart. There are 1–64 unique exact
release tuples: `extension_id`, `extension_version`, `companion_version`,
`companion_platform`, `companion_arch`. Stable semantic versions and the
independent native 2.12.0 floor are mandatory.

`TRUSTED_RELEASE_KEYS` contains only reviewed public Ed25519 roots, keyed by ID
with canonical base64 32-byte public keys. The reviewed `publisher-2026` root is
pinned in source; development and fixture roots are not accepted. This pin is
not a signed release approval: a genuine, currently valid policy must still be
supplied independently. Policy contents never supply their own root.
Missing/expired/invalid signatures or unmatched tuples fail closed on
every admission lookup. Public presentation catalog metadata is not evidence.

A universal2 Mac release uses two exact runtime tuples, `darwin/aarch64` and
`darwin/x86_64`, because each executing slice reports its runtime architecture.
This does not change the native catalog's `macos/universal2` artifact identity.
Each tuple retains the exact approved extension/native versions and production
extension ID. No platform-group, origin, URL, digest or Docker field is added to
this policy schema. Loopback server URL and rollout remain separate settings.

This server allowlist does not inspect or attest host executable bytes; the
native host independently enforces its signed installer/release chain. It
does not replace pairing, selection, heartbeat, cutover, or transport checks.
