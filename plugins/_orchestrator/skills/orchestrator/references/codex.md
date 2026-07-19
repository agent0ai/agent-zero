# Codex CLI

Use Codex for autonomous coding tasks in a repository. Inside the Agent Zero Docker runtime, the Codex sandbox may fail, so the Docker-safe default uses `--dangerously-bypass-approvals-and-sandbox`.

## Install And Probe

```bash
command -v codex >/dev/null || npm install -g @openai/codex
codex --version
```

## Optional Plugin-Owned Login

If the settings screen connected Codex with plugin-owned device login, run Codex with:

```bash
export CODEX_HOME=/a0/usr/plugins/_orchestrator/data/codex
```

If Codex reports missing auth, prefer the plugin settings device-code login when available. Otherwise run `codex login`, relay the device/browser instructions to the user, wait for confirmation, and retry the smoke prompt.

## Smoke Prompt

```bash
cd "$WORKDIR"
codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox "Respond exactly: TERMINAL_AGENT_SMOKE_OK"
```

## Real Task

```bash
cd "$WORKDIR"
codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox "$TASK"
```

If the runtime supports Codex's own sandbox, omit `--dangerously-bypass-approvals-and-sandbox`. If the settings screen has a model override, add `-m "$MODEL"`.
