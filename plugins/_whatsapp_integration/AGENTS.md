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
- Do not leave unmanaged bridge services outside plugin-owned runtime paths.

## Work Guidance

- Coordinate Node bridge changes with Python bridge client and settings UI.

## Verification

- Smoke-test dependency install, bridge start, QR pairing, allowed-number filtering, message routing, and replies when practical.

## Child DOX Index

No child DOX files.
