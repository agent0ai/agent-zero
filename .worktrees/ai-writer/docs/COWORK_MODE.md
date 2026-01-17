# Cowork Mode

Cowork mode adds folder scoping and an approval workflow for impactful agent actions.

## What It Does

- Restricts file access to an allowlist of folders.
- Prompts for approval before impactful actions (shell, email, memory edits, scheduling, browser agent).
- Applies approvals per chat thread and can inherit to subagents.

## Configure

1. Open Settings → Agent → Cowork Mode.
2. Enable Cowork mode.
3. Add allowed folders in the Cowork Manager.
4. (Optional) Edit the impactful tools list to match your workflow.

## Approvals

- Open Cowork Manager to see pending approvals for the current thread.
- Approve or deny actions as they appear.
- Use "Approve & Retry" to nudge the agent to re-attempt the action immediately.
- Use "Clear Resolved" to remove finished approvals.
- Use the "Apply to subagents" toggle to scope approvals to a single agent or the whole chain.

## Notes

- Approvals are recorded per thread (context) and are not shared across chats.
- If no allowed folders are configured, no folder restriction is enforced.
- The top status bar shows Cowork status, allowed folder count, and pending approvals.
