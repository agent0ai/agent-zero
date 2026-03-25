---
    title: "🔒 Security: Implement encrypted secrets storage"
    labels: "security, high-priority, enhancement"
    ---

    ## Problem Statement

    Currently, Agent Zero stores all secrets (API keys, passwords, tokens) in plaintext in `usr/secrets.env`. This is a **critical security vulnerability** that exposes credentials to:

    - Anyone with filesystem access to the Docker volume
    - Backup files that may be stored unencrypted
    - Container escape scenarios
    - Insider threats

    ## Current Implementation

    - Secrets stored as plain key-value pairs in `.env` format
    - No encryption at rest
    - No secrets rotation mechanism
    - Uses `dotenv.get_dotenv_value()` throughout codebase

    ## Proposed Solution

    ### Option A: Docker Secrets (Recommended for Docker deployments)
    - Store secrets in Docker swarm secrets
    - Mount as in-memory filesystem (`/run/secrets/`)
    - Access via secret name, not file path
    - Automatic rotation support

    ### Option B: OS Keyring/Secret Service
    - Use `keyring` library for cross-platform secret storage
    - Fall back to encrypted file if keyring unavailable
    - Supported backends: GNOME Keyring, KWallet, macOS Keychain, Windows DPAPI

    ### Option C: External Vault (Enterprise)
    - HashiCorp Vault
    - AWS Secrets Manager
    - Azure Key Vault
    - GCP Secret Manager

    ## Implementation Requirements

    - [ ] Encrypt all secrets at rest
    - [ ] Provide migration path from existing plaintext secrets
    - [ ] Maintain backward compatibility during transition
    - [ ] Add secrets rotation capability
    - [ ] Audit log for secret access
    - [ ] Secrets should never appear in logs or error messages
    - [ ] Support for multiple secret backends (pluggable)

    ## Affected Components

    - `python/helpers/secrets.py` (needs creation)
    - `python/helpers/rfc_exchange.py` (password retrieval)
    - `python/tools/code_execution_tool.py` (SSH password usage)
    - All tools that access `DOTENV` values

    ## Testing Requirements

    - [ ] Unit tests for encryption/decryption
    - [ ] Integration tests with each backend
    - [ ] Migration tests (plaintext → encrypted)
    - [ ] Security tests: verify secrets not in logs
    - [ ] Performance benchmarks (encryption overhead)

    ## Acceptance Criteria

    1. No plaintext secrets stored on disk
    2. Existing functionality preserved (secrets still accessible to tools)
    3. Migration tool provided to convert existing secrets
    4. Documentation updated with new secret management procedures
    5. Security audit passed (no credentials in logs, proper permissions)

    ## Additional Notes

    - This is a **breaking change** for direct `.env` file edits
    - Consider providing a compatibility mode that reads from both locations during transition
    - Recommended to implement alongside **container security hardening** PR
    