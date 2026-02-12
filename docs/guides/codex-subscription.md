# Codex (ChatGPT Subscription) Guide

This guide explains how to use Agent Zero with your ChatGPT subscription through the `Codex (ChatGPT subscription)` provider.

## What This Integration Does

- Uses local `codex` CLI authentication (your ChatGPT account), not OpenAI API billing.
- Supports independent model selection for:
  - Chat model
  - Utility model
  - Browser model
- Keeps embedding model unchanged (embedding does not use Codex subscription mode).
- Uses one global login, then lets you choose different models per role.

## Prerequisites

- `codex` CLI is installed and available in PATH.
- You can run:

```bash
codex --version
codex login status
```

- Agent Zero is running and you can open the Web UI settings.

## UI Walkthrough

### 1. Open Agent Settings

- Go to **Settings → Agent Settings**.
- You should see sections for `Chat Model`, `Utility model`, `Web Browser Model`, and `ChatGPT Subscription`.

![Agent settings overview](../res/setup/codex/agent-settings-overview.svg)

### 2. Connect Your ChatGPT Subscription (Global Login)

- Open **ChatGPT Subscription** section.
- Click **Connect ChatGPT**.
- Complete authentication in the browser window opened by the login flow.
- Click **Check Status** and confirm:
  - Installed: `yes`
  - Logged in: `yes`
  - Login flow: `completed`
- Click **Refresh Models** to fetch available Codex models for your account.

![Subscription login panel](../res/setup/codex/subscription-panel.svg)

> [!NOTE]
> This login is global and shared by all Codex-backed roles. You do not log in separately for Chat/Utility/Browser.

### 3. Set Providers and Models Per Role

For each section below, set provider to `Codex (ChatGPT subscription)`:

- **Chat Model**
- **Utility model**
- **Web Browser Model**

Then choose model name independently per role. Example:

- Chat model: `gpt-5.2-codex`
- Utility model: `gpt-5.1-codex-mini`
- Browser model: `gpt-5.2`

Click **Save**.

![Per-role model selectors](../res/setup/codex/per-role-models.svg)

## How It Works Internally

- Agent Zero runs Codex through local CLI (`codex exec --json`) for Chat/Utility/Browser roles.
- A single ChatGPT login is reused globally.
- Each role stores its own model setting (`chat_model_name`, `util_model_name`, `browser_model_name`).
- Codex sessions are resumed per chat context and per role:
  - New chat starts fresh Codex thread(s).
  - Existing chat resumes relevant Codex thread for that role.
- If Codex fails on a call, Agent Zero attempts a temporary per-call fallback to the previous non-Codex provider for that role and shows a warning banner.
- Saved provider remains `codex` unless you change it manually.

## Verify It Works (Checklist)

### A. UI Verification

- [ ] Chat role shows selected Chat model name correctly.
- [ ] Utility role shows selected Utility model name correctly.
- [ ] Browser role shows selected Browser model name correctly.
- [ ] Reopening Settings still shows all three chosen values.

### B. Backend Verification

Run:

```bash
cd agent-zero
./.venv/bin/python - <<'PY'
from python.helpers import settings
s=settings.get_settings()
print("chat:", s["chat_model_name"])
print("util:", s["util_model_name"])
print("browser:", s["browser_model_name"])
PY
```

Expected: values match what you selected in UI for each role.

### C. Functional Verification

- Send a normal chat prompt and confirm response arrives.
- Trigger at least one utility-style task (summarization/memory operations) and verify no model misformat loop.
- Trigger browser-use task and verify browser path still works.

## Security Notes

> [!CAUTION]
> This setup can run Codex in unrestricted full-auto mode (`--dangerously-bypass-approvals-and-sandbox`), which can execute commands without additional sandbox/approval prompts. Use only in trusted environments.

> [!IMPORTANT]
> ChatGPT subscription login is not an API key replacement for non-Codex providers. If you switch back to OpenAI/OpenRouter/etc, configure API keys as usual.

## Common Issues

### UI shows the same model for all three roles

- First verify backend values (command above).
- If backend values are different, update to the latest UI patch and hard-refresh browser.
- If mismatch persists, reopen settings after save and check model text fields again.

### Codex status says not connected

- Confirm `codex` is installed on the same machine/container where Agent Zero backend runs.
- Run `codex login status` in terminal.
- Return to **ChatGPT Subscription** and click **Check Status**.

### No model list appears

- Ensure login is completed first.
- Click **Refresh Models**.
- If still empty/unverified, use manual model entry (exact model ID) and re-check diagnostics in status panel.

## Recommended Team Documentation Practice

If you maintain a fork/team deployment:

1. Keep this guide (`docs/guides/codex-subscription.md`) as the detailed source of truth.
2. Keep README concise with a link to this guide.
3. Add short troubleshooting bullets in `docs/guides/troubleshooting.md`.
4. When UI changes, update screenshots in `docs/res/setup/codex/`.

