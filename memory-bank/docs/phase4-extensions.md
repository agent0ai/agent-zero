# Phase 4 — Pentest Extensions

## Status: COMPLETE

## What Was Done

Created four extensions under `agents/hacker/extensions/`. Extensions are profile-specific and only run for the hacker agent. They provide: scope enforcement, engagement context injection, auto-save reminders, and session restore on init.

---

## Extensions Created

### `tool_execute_before/_05_scope_enforcement.py`

**Hook:** `tool_execute_before` — runs before every tool call.

**What it does:**
1. Checks if the called tool is a network-touching tool (`code_execution_tool`, `browser_agent`, `search_engine`)
2. Extracts all IPs, domains, and URLs from the tool arguments using regex
3. Looks up the active engagement by scanning the `engagements/` directory for the most recently modified `engagement.json`
4. Loads `scope.txt` for that engagement
5. Calls the same `is_in_scope()` function used by the `scope_check` tool
6. If any extracted target is out of scope: logs a warning and injects a `scope_warning` into `extras_temporary` so the agent sees it before its next action

**Design choice:** Does NOT hard-block execution (does not raise an exception). Instead, it injects a visible warning. This is intentional — hard blocking would break legitimate use cases (e.g., querying the NVD website, running a local tool that happens to mention an external IP in its output). The agent remains responsible for interpreting the warning.

**File ordering:** Named `_05_` so it runs before any existing `_10_` extensions (the framework sorts by filename).

---

### `agent_init/_20_load_engagement.py`

**Hook:** `agent_init` — runs once when the hacker agent is first created.

**What it does:**
1. Scans `engagements/` for the most recently accessed engagement (by `engagement.json` mtime)
2. Reads scope entries, finding counts by severity, and RoE preview
3. Logs the summary to the UI via `self.agent.context.log.log()`
4. Injects the summary into `extras_persistent` so it persists through the session

**Why persistent extras:** `extras_persistent` survives across message loop iterations (unlike `extras_temporary`). This means the engagement context stays in the system prompt for the entire session without re-loading from disk every iteration.

---

### `message_loop_prompts_after/_80_include_engagement_context.py`

**Hook:** `message_loop_prompts_after` — runs after message loop prompts are assembled.

**What it does:**
- Finds active engagement (same mtime-based detection as `_20_load_engagement.py`)
- Reads scope entry count and preview, finding counts by severity
- Injects a one-block "Current Engagement" summary into `extras_temporary`

**What the agent sees every iteration:**
```
## Current Engagement
Target: 10.10.10.5 | Scope: 2 entries (10.10.10.5, 10.10.10.0/24) | Findings: 3 total — 1 Critical | 1 High | 1 Medium
Workspace: /a0/usr/workdir/engagements/10.10.10.5
```

**File ordering:** Named `_80_` to run after the built-in `_70_include_agent_info.py`, ensuring engagement context is the last piece of context injected.

---

### `monologue_end/_55_auto_save_findings.py`

**Hook:** `monologue_end` — runs after each complete agent response.

**What it does:**
1. Scans the last 5 messages for text containing vulnerability indicators (CVE IDs, "vulnerable", "exploited", "uid=0", credential patterns, etc.)
2. Checks whether `findings_tracker` was already called in this monologue
3. If indicators found AND tracker was NOT called: injects a reminder into `extras_temporary` prompting the agent to log the finding before continuing

**Pattern list:** 12 regex patterns covering CVE mentions, exploitation terminology, shell proof strings (uid=0, whoami root), and credential discovery phrases.

**Why this matters:** Agents tend to get absorbed in the technical exploitation flow and skip logging. This extension catches those cases by pattern-matching their own output and nudging them back to the `findings_tracker`.
