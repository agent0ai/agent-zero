# Passkey (WebAuthn) Integration Guide

Agent Jumbo now supports **Hardware-Bound Authentication** using Passkeys. This allows you to centralize all authorization via your phone or hardware security key (like YubiKey), providing a seamless "Power User" experience.

## Key Features

- **Passwordless Login**: Use your phone's biometrics (FaceID/TouchID) to access the UI.
- **Mandatory Tool Authorization**: Requirement for hardware confirmation before sensitive tools (Terminal, Email, Files) are executed.
- **Vault Protection**: Decrypt secrets only after hardware verification.

## Setup Instructions

1. **Prerequisites**:
   - Ensure you are accessing Agent Jumbo over **HTTPS** (or `localhost` for local development). Passkeys require a "Secure Context".
   - Using a tunnel (like Cloudflare or Tailscale) automatically provides the necessary secure context.

2. **Registration**:
   - Open **Settings** -> **Authentication** tab.
   - Look for the **Hardware Security (Passkeys)** section.
   - Click **"Register My Phone"**.
   - Your browser will prompt you to create a passkey. Choose "Use a phone or tablet" or "This device".
   - Complete the biometric scan on your phone.

3. **Verification**:
   - Once registered, your phone is bound to your Agent Jumbo instance.
   - You can now enable "Mandatory Tool Authorization" to ensure the agent never sends an email or runs a shell command without a physical tap on your device.

## Technical Details

- **Protocol**: FIDO2 / WebAuthn L3
- **Storage**: Public keys are stored in `data/workflow.db` (Table: `user_passkeys`).
- **Engine**: Powered by the `webauthn` Python library.

---
*Created by GitHub Copilot*
