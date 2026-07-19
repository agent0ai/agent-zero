# Agent Profiles

Agent Profiles change the voice, habits, and prompt instructions driving the
current chat.

Use a profile when you want Agent Zero to behave like a researcher, developer,
security reviewer, writing partner, data analyst, or another repeatable working
style.

For architecture and source-linked internals, use
[DeepWiki for Agent Zero](https://deepwiki.com/agent0ai/agent-zero).

## Switch Profile In A Chat

The profile menu lives in the status bar near the chat input.

![Agent Profile selector](../res/usage/webui/agent-profile-selector.png)

1. Open a chat.
2. Click the current profile name near the chat input.
3. Choose the profile you want.
4. Continue the chat normally.

The change applies to the selected chat. Other chats can keep their own profile.

> [!TIP]
> Use **Settings -> Agent Config** when you want to change the default profile
> for new chats.

## Create A New Agent Profile

The same menu includes **Create new Agent Profile**.

![Create Agent Profile prompt](../res/usage/webui/agent-profile-create-prompt.png)

When you click it, Agent Zero places a ready-to-send message in the chat input.
Send that message and Agent Zero starts a guided profile-creation flow.

The flow is intentionally conversational:

- it asks what the new profile should be excellent at;
- it suggests sensible defaults;
- it confirms a compact summary before creating anything;
- it uses the dedicated profile-creation skill to keep the process tidy.

Good answers are practical:

```text
This profile should help me plan YouTube scripts for technical demos. It should
ask for the target audience, keep the tone simple, and suggest a visual outline.
```

```text
I want a cautious finance analyst profile. It should separate facts from
assumptions, prefer spreadsheets, and never present estimates as certainty.
```

## Profile, Skill, Project, Or Model Preset?

These controls are related, but they solve different problems.

| Use this | When you want to change |
| --- | --- |
| **Agent Profile** | The agent's role, tone, workflow, and prompt instructions. |
| **Skill** | A specific procedure or capability the agent should keep available. |
| **Project** | Files, workspace, memories, instructions, secrets, and long-running context. |
| **Model Preset** | Which models are used for the chat. |

Example:

- use a **Project** for a client repository;
- use an **Agent Profile** for "careful code reviewer";
- pin a **Skill** for a repeated workflow;
- choose a **Model Preset** for speed, cost, or maximum capability.

## Small Advanced Note

Most users should create profiles through the menu above.

If you edit files directly, custom profiles normally live in:

```text
/a0/usr/agents/<profile-name>/
```

Custom prompts belong inside that profile's `prompts/` folder. Keep direct file
edits small and documented so updates remain easy to understand later.

For deeper file layout and prompt-loading details, use
[DeepWiki for Agent Zero](https://deepwiki.com/agent0ai/agent-zero).
