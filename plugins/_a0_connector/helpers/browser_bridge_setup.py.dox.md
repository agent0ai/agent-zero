# Browser setup projection

Read-only public setup guidance for Browser settings. Compose the configured production extension ID with the instance `available` rollout gate; neither config nor links imply a live runtime or a published Web Store item. Return no extension link or installer when this setup gate is off.

Installer links come only from the existing strict, compatible server-configured release presentation metadata. That is not cryptographic verification or an availability probe: the browser-host installer still verifies the signed catalog and selected artifact against its own publisher root before execution. Never synthesize absent OS artifacts or place the native companion inside Docker. No request-selected URL, platform override, credential, filesystem path, download, pairing, selection or install effect is accepted here.

The exact `a0.browser-bridge.setup.v1` projection states `browser_control_ready: false`, `install_target: browser_host`, and `host_verification_required: true`; each installer has only platform, architecture and canonical HTTPS URL. Keep the three OS choices visible in the client even when no release exists for one of them.
