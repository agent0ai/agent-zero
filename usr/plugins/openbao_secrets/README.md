# OpenBao Secrets Plugin for Agent Zero

Replaces Agent Zero's default `.env`-based secrets management with [OpenBao](https://openbao.org/) KV v2 as the secrets backend.

## Status

**v0.1.0 — Replace Mode** (in development)

> **Dependency:** Requires upstream PR [agent0ai/agent-zero#1246](https://github.com/agent0ai/agent-zero/pull/1246) to be merged (adds `@extensible` decorator to secrets factory functions).

## Architecture

### How It Works

This plugin uses Agent Zero's `@extensible` decorator system to intercept the three secrets factory functions:

| Factory Function | Extension Point | Callers |
|---|---|---|
| `get_secrets_manager()` | `helpers_secrets_get_secrets_manager_start` | log, print_style, browser_agent |
| `get_default_secrets_manager()` | `helpers_secrets_get_default_secrets_manager_start` | settings.py |
| `get_project_secrets_manager()` | `helpers_secrets_get_project_secrets_manager_start` | projects.py |

Each extension intercepts the factory call at `_start` and sets `data["result"]` to an `OpenBaoSecretsManager` instance, short-circuiting the default `.env`-based manager.

### Fallback Chain

```
OpenBao KV v2 → .env file → empty dict (with error logging)
```

If OpenBao is unreachable (circuit breaker open, connection timeout), the plugin gracefully degrades to `.env` files with a logged warning.

### Resilience Stack

| Pattern | Library | Purpose |
|---|---|---|
| Retry | `tenacity` | Exponential backoff + jitter for transient failures |
| Circuit Breaker | `circuitbreaker` | Fail-fast when OpenBao is down |
| TTL Cache | Built-in | Avoid per-request API calls |
| Timeout | `httpx` | Bounded HTTP operations |
| Token Renewal | `hvac` | Lazy renewal on 403 / near-expiry |

## Configuration

### Environment Variables (highest priority)

| Variable | Default | Description |
|---|---|---|
| `OPENBAO_ENABLED` | `false` | Enable the OpenBao backend |
| `OPENBAO_URL` | `http://127.0.0.1:8200` | OpenBao server URL |
| `OPENBAO_AUTH_METHOD` | `approle` | `approle` or `token` |
| `OPENBAO_ROLE_ID` | | AppRole role ID |
| `OPENBAO_SECRET_ID` | | AppRole secret ID |
| `OPENBAO_TOKEN` | | Direct token (if auth_method=token) |
| `OPENBAO_MOUNT_POINT` | `secret` | KV v2 mount point |
| `OPENBAO_SECRETS_PATH` | `agentzero` | Path within mount |
| `OPENBAO_TLS_VERIFY` | `true` | Verify TLS certificates |
| `OPENBAO_TLS_CA_CERT` | | Path to CA certificate bundle |
| `OPENBAO_TIMEOUT` | `10.0` | HTTP timeout (seconds) |
| `OPENBAO_CACHE_TTL` | `300` | Cache time-to-live (seconds) |
| `OPENBAO_RETRY_ATTEMPTS` | `3` | Max retry attempts |
| `OPENBAO_CB_THRESHOLD` | `5` | Circuit breaker failure threshold |
| `OPENBAO_CB_RECOVERY` | `60` | Circuit breaker recovery (seconds) |
| `OPENBAO_FALLBACK_TO_ENV` | `true` | Fall back to .env on failure |

### Settings File (lower priority)

Place a `settings.json` in the plugin directory with the same keys (snake_case).

## OpenBao Target

| Parameter | Value |
|---|---|
| Version | v2.4.4 (latest stable) |
| Secrets Engine | KV v2 (versioned) |
| Auth Method | AppRole (primary), Token (fallback) |
| Python Client | `hvac` (Vault API-compatible) |
| Docker Image | `ghcr.io/openbao/openbao:2.4.4` |

## Project Structure

```
plugin.yaml                 # Plugin metadata
requirements.txt            # Python dependencies
helpers/
  config.py                 # Configuration loading and validation
  openbao_client.py         # Resilient hvac client wrapper
  openbao_secrets_manager.py # SecretsManager subclass
extensions/python/
  helpers_secrets_get_secrets_manager_start/
    _10_openbao_factory.py
  helpers_secrets_get_default_secrets_manager_start/
    _10_openbao_default_factory.py
  helpers_secrets_get_project_secrets_manager_start/
    _10_openbao_project_factory.py
api/
  health.py                 # Health check endpoint
webui/
  config.html               # Settings UI
tests/
  test_config.py            # Configuration tests
  test_openbao_client.py    # Client tests (stub)
  test_openbao_manager.py   # Manager tests (stub)
```

## Development

### Prerequisites

```bash
pip install hvac tenacity circuitbreaker pytest
```

### Run Tests

```bash
pytest tests/ -v
```

## Issue Tracker

See [Gitea milestone v0.1.0](http://192.168.200.52:3000/deimosAI/a0-plugin-openbao-secrets/milestone/17) for all planned work.

## License

MIT
