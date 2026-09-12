# WhatsApp Integration Plugin DOX

## Purpose

- Own WhatsApp communication through a Baileys-based Node.js bridge.

## Ownership

- `helpers/bridge_manager.py` owns bridge lifecycle.
- `helpers/handler.py` and `helpers/wa_client.py` own message routing and bridge API interaction.
- `helpers/storage_paths.py`, attachment helpers, and number utilities own storage, attachment, and phone-number handling.
- `whatsapp-bridge/` owns the Node.js bridge package.
- `api/`, `prompts/`, `extensions/`, `default_config.yaml`, `plugin.yaml`, `README.md`, and `webui/` own QR/start/disconnect/test endpoints, prompt fragments, hooks, settings, metadata, docs, and UI.

## Local Contracts

- Treat WhatsApp sessions, QR data, phone numbers, attachments, and bridge state as sensitive.
- Keep allowed-number and group-response controls enforced.
- Enforce sender and group authorization in the bridge before downloading media, and contain every media write beneath the configured cache directory.
- Keep Python dispatch checks and number normalization; propagate normalized authorization settings through all bridge startup paths and restart on policy changes.
- Do not leave unmanaged bridge services outside plugin-owned runtime paths.
- Use the shared project/profile scope selector and Advanced accordion. Configuration is the sole plugin UI; keep pairing and connection controls there.

## Work Guidance

- Coordinate Node bridge changes with Python bridge client and settings UI.
- Pairing starts on one explicit Show QR code action, which enables the draft configuration. Keep QR polling sequential and ignore responses after cancellation or modal cleanup; saving remains owned by the settings wizard.

## Verification

- Run `node --test tests/test_whatsapp_bridge.mjs` and `pytest tests/test_whatsapp_bridge_manager.py tests/test_whatsapp_number_utils.py tests/test_whatsapp_storage_paths.py` from the repository root.
- Run `node --test tests/test_whatsapp_config_store.mjs` for pairing lifecycle changes; verify the two-column pairing layout and its mobile stack in the WebUI.
- Smoke-test dependency install, bridge start, QR pairing, allowed-number filtering, message routing, and replies when practical.

## Child DOX Index

No child DOX files.
