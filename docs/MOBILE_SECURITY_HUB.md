# Agent Jumbo: Mobile-First Security Hub & Identity Platform

## 1. Executive Summary

The **Mobile-First Security Hub** transforms Agent Jumbo from a localized AI assistant into a hardware-secured, proactive autonomous agent. By integrating hardware-bound biometric authentication (Passkeys) and a cryptographic sidecar, the agent ensures that high-risk operations are always verified by the physical owner, while proactively monitoring its own behavior for anomalies.

---

## 2. Core Security Services

### 🔒 Identity & Auth (Passkeys)

* **Hardware-Bound Verification**: Replaces generic passwords with **WebAuthn (FIDO2)** passkeys. Users authenticate using TouchID, FaceID, or physical TPMs (Titan/YubiKey).
* **Hardware Attestation**: Enforces `STRICT_HARDWARE_ONLY` mode, verifying that the authenticator is a physical secure enclave rather than a software emulator.
* **Session Gating**: High-risk tools (Bash, Email, File Deletion) are locked by default and require a fresh biometric signature every 60 minutes.

### 🛡️ The Security Manager

* **Behavioral Heuristics (Traffic Sentinel)**: Monitors execution velocity. If the agent attempts more than 15 actions per minute, it triggers an automatic **Panic Lock** to prevent infinite loops or hijacking.
* **Network Sentinel**: Intercepts tool arguments for unauthorized outbound activity (e.g., hidden `curl` or `wget` calls). Suspicious network calls trigger an immediate push notification for manual approval.
* **Rate Limiting**: Protects all security APIs from brute-force attempts using an IP-based windowed limiter.

### 📦 Proactive Push & Actionable Alerts

* **VAPID Signed Messaging**: Uses a secure push protocol to communicate with registered mobile devices even when the Web UI is closed.
* **Actionable Notifications**: Notifications include **Approve** and **Deny** buttons. Users can authorize a blocked tool directly from their phone's lock screen without opening any app.
* **Device Nudges**: Monitors phone state (battery level, sync status) and proactive context (high-risk tool use) to keep the user informed.

### 🔐 Zero-Knowledge Storage Vault

* **AES-256-GCM Encryption**: All sensitive platform secrets and user data are encrypted at rest using a key derived from the hardware-bound platform secret.
* **Cryptographic Sidecar**: The `SecurityVaultManager` handles the lifecycle of platform keys (VAPID, Storage Master) in a dedicated secure store.

---

## 3. Key Features

### 🚨 Panic Lock

A digital "Dead Man's Switch." With one tap (UI or API), all authorized sessions are revoked, all pending requests are cleared, and the agent is frozen until the user re-authenticates via a physical Passkey.

### 📱 Profile & Device Sync

* **Cross-Device Heartbeat**: Real-time syncing of battery status and security configuration between the host machine and the mobile device.
* **Unified Identity**: Allows a single hardware key to manage authorization across multiple agent instances.

### 🕵️ Security Audit Logging

A tamper-resistant ledger tracking every security event:

* Passkey registration/verification.
* Unauthorized tool attempts.
* Heuristic anomaly detections.
* IP-address and User-Agent fingerprinting for every verification.

---

## 4. Technical Architecture

| Component | Technology |
| :--- | :--- |
| **Identity** | WebAuthn (FIDO2), P-256 ECDSA |
| **Push** | VAPID, Web Push Protocol, Service Workers |
| **Encryption** | AES-256-GCM (Authenticated Encryption) |
| **Backend** | Python, pywebauthn, pywebpush, flask |
| **Frontend** | Alpine.js, PWA Manifest, Cache API |

---

## 5. API Reference (Internal)

* `POST /passkey_auth`: Manages the WebAuthn challenge/response handshake.
* `POST /security_ops`: Handles Panic Lock and Audit Log retrieval.
* `POST /profile_sync`: Updates device telemetry and battery health.
* `POST /security_tool_action`: Endpoint for remote notification approvals.

---

## 6. Security Advisory

This hub is designed as a **White-Hat Protection Layer**. While it significantly hardens the agent, users should always monitor `ENFORCE_PASSKEY` settings. In `Strict` mode, the agent becomes a high-assurance tool suitable for production environments.
