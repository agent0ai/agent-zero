# Claude Code

Use Claude Code in print mode. Skip permissions is the default non-interactive mode only when the shell is not root; Claude Code rejects that mode under root/sudo.

## Install And Probe

```bash
command -v claude >/dev/null || npm install -g @anthropic-ai/claude-code
claude --version
claude auth status || true
```

## Smoke Prompt

```bash
cd "$WORKDIR"
if [ "$(id -u)" -eq 0 ]; then
  claude -p "Respond exactly: TERMINAL_AGENT_SMOKE_OK" --output-format json
else
  claude -p "Respond exactly: TERMINAL_AGENT_SMOKE_OK" --output-format json --permission-mode bypassPermissions --allowedTools Bash,Read,Edit
fi
```

## Login

If Claude Code reports `Not logged in` or asks for `/login`, do not open the TUI. First ask the user which auth mode to use:

1. Claude subscription: `claude auth login --claudeai`
2. Anthropic Console/API billing: `claude auth login --console`
3. SSO: `claude auth login --sso`
4. API key outside chat: ask the user to open Settings > External Services > Secrets Management and enter the key in `/a0/usr/.env`, right after `ANTHROPIC_API_KEY=`. The Agent Zero `.env` file is `/a0/usr/.env`, not `$WORKDIR/.env`.

After the user chooses, run only that command and relay its browser/device instructions. If the user gives an email to prefill, add `--email "<email>"`. Wait for confirmation, then retry the smoke prompt. Do not redirect them to a Docker shell just to choose a menu option. Do not start plain `claude` for login; it opens the first-run TUI (theme/provider menus) and is not a safe agent-driven login surface. Do not run bare `claude auth login` when provider choice is still unknown.

If a previous attempt already opened plain `claude` and the terminal shows theme/provider menus or no readable login URL, stop. Reset that terminal session; do not press Enter, do not send `/login`, and do not keep polling the stuck TUI. Then ask for the auth mode above and run the matching `claude auth login ...` command in a fresh terminal session.

## Agent Zero Secrets

When using an API key from Agent Zero secrets, source `/a0/usr/.env` without printing it. Some Agent Zero installs store the Anthropic key as `API_KEY_ANTHROPIC`; map it to the CLI variable before running Claude Code:

```bash
set -a
. /a0/usr/.env
set +a
[ -z "${ANTHROPIC_API_KEY:-}" ] && [ -n "${API_KEY_ANTHROPIC:-}" ] && export ANTHROPIC_API_KEY="$API_KEY_ANTHROPIC"
```

## Real Task

Replace the smoke prompt with `$TASK`.
