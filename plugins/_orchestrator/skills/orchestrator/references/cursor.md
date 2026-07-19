# Cursor CLI

Use Cursor CLI for headless Cursor Agent tasks. The official binary is `agent`; running it without `-p` starts the interactive terminal UI, so use `agent -p` for Agent Zero delegation.

## Install And Probe

```bash
command -v agent >/dev/null || curl https://cursor.com/install -fsS | bash
agent --version
agent status || true
```

## Smoke Prompt

```bash
cd "$WORKDIR"
agent -p --output-format text "Respond exactly: TERMINAL_AGENT_SMOKE_OK"
```

## Login

For scripts and containers, prefer API-key auth:

```bash
export CURSOR_API_KEY="..."
```

Do not ask the user to paste the key into chat. Ask them to set `CURSOR_API_KEY` in the runtime environment, or to add it through Settings > External Services > Secrets Management when that maps into `/a0/usr/.env`.

When using Agent Zero secrets, source `/a0/usr/.env` without printing it. If the key is stored as `API_KEY_CURSOR`, map it to the CLI variable before running Cursor CLI:

```bash
set -a
. /a0/usr/.env
set +a
[ -z "${CURSOR_API_KEY:-}" ] && [ -n "${API_KEY_CURSOR:-}" ] && export CURSOR_API_KEY="$API_KEY_CURSOR"
```

For browser login in a container or remote terminal, run:

```bash
NO_OPEN_BROWSER=1 agent login
```

Relay the printed URL to the user, wait for confirmation, then retry the smoke prompt. Use `agent status` to check auth and `agent logout` only when the user explicitly asks to clear Cursor CLI credentials.

## Real Task

```bash
cd "$WORKDIR"
agent -p --force --output-format text "$TASK"
```

Use `--output-format json` when the caller needs structured output, or `--output-format stream-json --stream-partial-output` when polling progress. Select models with Cursor CLI's `/model` command in an interactive setup, not with an invented flag.
