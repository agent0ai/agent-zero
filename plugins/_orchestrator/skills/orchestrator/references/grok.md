# Grok Build

Use Grok Build for headless xAI coding-agent tasks. Running `grok` with no arguments starts the interactive TUI, so use `-p` for Agent Zero delegation.

## Install And Probe

```bash
command -v grok >/dev/null || curl -fsSL https://x.ai/cli/install.sh | bash
grok version || grok --version || grok --help
```

If the installer host is blocked, use the official npm distribution instead:

```bash
npm install -g @xai-official/grok
```

## Smoke Prompt

```bash
grok --no-auto-update --cwd "$WORKDIR" -p "Respond exactly: TERMINAL_AGENT_SMOKE_OK" --output-format json --always-approve --no-alt-screen
```

## Login

If Grok Build needs auth, prefer API-key auth for headless automation:

```bash
export XAI_API_KEY="xai-..."
```

Do not ask the user to paste the key into chat. Ask them to set `XAI_API_KEY` in the runtime environment, or to add it through Settings > External Services > Secrets Management when that maps into `/a0/usr/.env`.

When using Agent Zero secrets, source `/a0/usr/.env` without printing it. Some Agent Zero installs store the xAI key as `API_KEY_XAI`; map it to the CLI variable before running Grok Build:

```bash
set -a
. /a0/usr/.env
set +a
[ -z "${XAI_API_KEY:-}" ] && [ -n "${API_KEY_XAI:-}" ] && export XAI_API_KEY="$API_KEY_XAI"
```

For account login in a container or remote terminal, run:

```bash
grok login --device-auth
```

Relay the printed URL and user code to the user, wait for confirmation, then retry the smoke prompt. Do not run bare `grok`; it opens the full-screen TUI.

## Real Task

```bash
grok --no-auto-update --cwd "$WORKDIR" -p "$TASK" --output-format json --always-approve --no-alt-screen
```

Add `-m "$MODEL"` only when the user or settings provide a model override. For session continuation, use `--session-id`, `--resume`, or `--continue` only when the user asks for it.
