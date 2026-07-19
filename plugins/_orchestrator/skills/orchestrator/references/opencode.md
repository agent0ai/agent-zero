# OpenCode

OpenCode has a non-interactive run mode suitable for this skill.

## Install And Probe

```bash
command -v opencode >/dev/null || curl -fsSL https://opencode.ai/install | bash
opencode --version || opencode --help
```

## Smoke Prompt

```bash
opencode run --dir "$WORKDIR" --auto "Respond exactly: TERMINAL_AGENT_SMOKE_OK"
```

## Login

If OpenCode needs auth, run `opencode auth login`, relay the provider/browser/key prompt to the user, wait for confirmation, and retry the smoke prompt. If that command is unavailable, run `opencode`, use `/connect`, and keep the same human-in-the-loop boundary.

## Real Task

Replace the smoke prompt with `$TASK`. Add `--model` or `--agent` only when the user or settings provide them.
