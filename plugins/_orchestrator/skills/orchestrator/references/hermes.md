# Hermes Agent

Use Hermes Agent for quiet headless chat. Skip approvals by default for non-interactive delegation.

## Install And Probe

```bash
command -v hermes >/dev/null || curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
hermes --version || hermes --help
```

## Smoke Prompt

```bash
cd "$WORKDIR"
hermes chat --quiet --source tool -q "Respond exactly: TERMINAL_AGENT_SMOKE_OK" --yolo
```

## Login

If Hermes needs setup, run `hermes setup --portal` when available, relay the OAuth/browser instructions to the user, wait for confirmation, and retry the smoke prompt. If it asks for a provider API key, have the user type it into the CLI prompt or set it as an environment variable outside chat.

## Real Task

Replace the smoke prompt with `$TASK`. Add `--model`, `--provider`, or `--toolsets` only when the user or settings provide them.
