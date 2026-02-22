# Agent Profiles

> **Navigation:** [Index](./index.md) | [Architecture](./architecture.md) | [Tools](./tools.md) | [Extensions](./extensions.md) | [Prompt System](./prompt-system.md) | [Configuration](./configuration.md)

---

## Profile System

A **profile** is a directory under `agents/` that selectively overrides the global framework defaults. A profile only needs to contain the files it wants to override — everything else falls back to the global `prompts/` directory.

### Profile directory structure

```
agents/<profile-name>/
├── agent.json              # Required: metadata (title, description, context)
├── _context.md             # Optional: human-readable description
├── settings.json           # Optional: settings overrides applied when profile is active
├── prompts/                # Optional: prompt file overrides
│   ├── agent.system.main.role.md
│   ├── agent.system.main.environment.md
│   ├── agent.system.main.communication.md
│   ├── agent.system.main.solving.md
│   └── agent.system.tool.<toolname>.md
├── extensions/             # Optional: extension overrides per hook
│   └── <hook_name>/
│       └── _NN_extension.py
└── tools/                  # Optional: profile-specific tools
    └── <toolname>.py
```

### How overrides work

When the agent assembles its system prompt and loads extensions:

1. **Prompts:** For every `{{ include "filename.md" }}`, the framework checks `agents/<profile>/prompts/` first, then `prompts/` global. First match wins.
2. **Extensions:** Both profile and global extensions run. If a profile extension has the same filename as a global one, only the profile version runs.
3. **Settings:** `agents/<profile>/settings.json` is merged on top of `usr/settings.json`.
4. **Tools:** Profile `tools/` directory is scanned alongside `python/tools/`.

### Selecting a profile

```bash
# Via Docker environment variable
A0_SET_agent_profile=hacker

# Via agents/<profile>/settings.json
{ "agent_profile": "hacker" }

# Via UI: Settings → Agent Profile
```

### Profile list

| Profile | Title | Purpose |
|---------|-------|---------|
| [agent0](#agent0) | Agent 0 | Default user-facing general assistant |
| [hacker](#hacker) | Hacker | ★ Autonomous penetration testing |
| [developer](#developer) | Master Developer | Complex software development |
| [researcher](#researcher) | Deep ReSearch | Research, analysis, reporting |
| [recon](#recon) | Recon Specialist | ★ Reconnaissance only (no exploitation) |
| [exploit-dev](#exploit-dev) | Exploit Developer | ★ Exploit research and payload generation |
| [reporter](#reporter) | Security Reporter | ★ Pentest report generation |
| [default](#default) | Default | Fallback profile with minimal overrides |
| [_example](#_example) | — | Template for building custom profiles |

★ = new profiles added in this project

---

## agent0

**Location:** `agents/agent0/`

The top-level user-facing agent. This is the profile users interact with directly. It emphasizes comprehensive, understandable output since the "superior" is a human, not another agent.

**Files:**
- `agent.json` — `"title": "Agent 0"`
- `prompts/agent.system.main.role.md` — general AI assistant, top-level, focus on comprehensible output, can delegate to specialized subordinates
- `prompts/agent.system.tool.response.md` — overrides the response tool documentation

**Unique behavior:** Only agents with `number == 0` show the initial greeting message. The `agent0` profile is what users see when they first open the UI.

---

## hacker

**Location:** `agents/hacker/`

The primary penetration testing agent. Runs the full engagement lifecycle from scope definition through report delivery. Orchestrates `recon`, `exploit-dev`, and `reporter` sub-agents.

**Files:**

```
agents/hacker/
├── agent.json              # "title": "Hacker"
├── _context.md
├── settings.json           # memory_subdir=hacker, profile=hacker
├── prompts/
│   ├── agent.system.main.role.md         # Full pentest methodology, 6 capability areas
│   ├── agent.system.main.environment.md  # Tool inventory table, wordlists, workspace structure
│   ├── agent.system.main.solving.md      # Pentest engagement loop, delegation rules, fallback table
│   ├── agent.system.main.communication.md # Output formats: action/finding/summary/subordinate
│   ├── agent.system.tool.engagement_init.md  # Tool docs: init workspace
│   ├── agent.system.tool.findings_tracker.md # Tool docs: CRUD findings
│   ├── agent.system.tool.scope_check.md      # Tool docs: validate scope
│   ├── agent.system.tool.report_generator.md # Tool docs: generate reports
│   └── agent.system.tool.cve_lookup.md       # Tool docs: CVE research
└── extensions/
    ├── agent_init/_20_load_engagement.py               # Restore engagement on session start
    ├── tool_execute_before/_05_scope_enforcement.py    # Warn on out-of-scope targets
    ├── message_loop_prompts_after/_80_include_engagement_context.py  # Inject engagement status
    └── monologue_end/_55_auto_save_findings.py         # Remind to log findings
```

### hacker — Role Summary

- **Identity:** Elite Penetration Tester, virtual employee of a cyber security company
- **Methodology:** Phase 0 (Scope) → 1 (Passive Recon) → 2 (Active Scan) → 3 (Vuln Analysis) → 4 (Exploit) → 5 (Post-Exploit) → 6 (Report)
- **Capabilities:** Network pentesting, web app testing, exploit development, post-exploitation, CVE research, professional reporting
- **Directives:** Always verify scope; load engagement context at session start; obey all instructions; high-agency retry mindset

### hacker — Environment

- Runtime: Kali Linux Docker, root access, Agent Zero at `/a0`
- Engagement workspace: `/a0/usr/workdir/engagements/<target>/`
- Tools: nmap/masscan/amass/theHarvester (recon), gobuster/ffuf/nikto/sqlmap/nuclei (web), metasploit/searchsploit/impacket (exploit), hashcat/john/hydra (passwords), linpeas/winpeas/bloodhound (post-exploit)
- Wordlists: `/usr/share/wordlists/rockyou.txt`, `/usr/share/seclists/`

### hacker — Settings (`settings.json`)

```json
{
  "agent_profile": "hacker",
  "agent_memory_subdir": "hacker",
  "workdir_path": "usr/workdir",
  "memory_recall_enabled": true,
  "memory_memorize_enabled": true
}
```

`agent_memory_subdir: "hacker"` isolates the hacker agent's FAISS index from other profiles, preventing cross-contamination of engagement data.

### hacker — Extensions

| Extension | Hook | Purpose |
|-----------|------|---------|
| `_20_load_engagement.py` | `agent_init` | Scans `engagements/` on startup, loads most recent engagement into `extras_persistent` |
| `_05_scope_enforcement.py` | `tool_execute_before` | Extracts IPs/domains from tool args, warns if out of scope |
| `_80_include_engagement_context.py` | `message_loop_prompts_after` | Injects target, scope count, finding counts into every prompt |
| `_55_auto_save_findings.py` | `monologue_end` | Pattern-matches response for CVE/exploit indicators, reminds to log findings |

See [extensions.md](./extensions.md#hacker-profile-extensions) for detailed docs.

### hacker — New Tools

| Tool | Purpose |
|------|---------|
| `engagement_init` | Initialize/manage engagement workspace |
| `findings_tracker` | CRUD for structured vulnerability findings |
| `scope_check` | Validate IP/domain/URL against scope.txt |
| `report_generator` | Generate MD/HTML/PDF pentest report |
| `cve_lookup` | NVD API + ExploitDB CVE research |

See [tools.md](./tools.md#pentest-tools) for full tool documentation.

---

## developer

**Location:** `agents/developer/`

Software development specialist with principal-level engineering expertise.

**Files:**
- `agent.json` — `"title": "Developer"`
- `prompts/agent.system.main.role.md` — "Agent Zero Master Developer", extensive role spec covering system architecture, full-stack implementation, DevOps, security engineering. Includes methodology steps and task examples (microservices, data pipelines, API platforms).
- `prompts/agent.system.main.communication.md` — Requires structured requirements elicitation interview before starting work. Detailed thinking format.

**Use case:** Delegate complex software development tasks from the hacker agent or directly as top-level agent for coding projects.

---

## researcher

**Location:** `agents/researcher/`

Research and analysis specialist with academic and corporate intelligence capabilities.

**Files:**
- `agent.json` — `"title": "Researcher"`
- `prompts/agent.system.main.role.md` — "Agent Zero Deep ReSearch", covers academic research, data analysis, market intelligence, compliance research. Multi-source validation, bias detection.
- `prompts/agent.system.main.communication.md` — Structured requirements elicitation, fact verification standards, output formats.

**Use case:** Use when you need thorough research on a target organization, CVE landscape, compliance requirements, or technical deep-dives.

---

## recon

**Location:** `agents/recon/`

Reconnaissance-only specialist. Explicitly cannot exploit — discovery and enumeration only.

**Files:**
- `agent.json` — `"title": "Recon Specialist"`
- `prompts/agent.system.main.role.md` — Passive OSINT (WHOIS, DNS, crt.sh, Shodan, theHarvester) + active recon (nmap, gobuster, ffuf, whatweb, sslscan, enum4linux-ng). Explicit constraint: "you do NOT exploit vulnerabilities". Structured output formats for port summaries, web fingerprints, and OSINT summaries.
- `prompts/agent.system.main.environment.md` — Tool table with key flags, wordlist paths, engagement workspace.

**Constraint by design:** The non-exploitation constraint prevents a delegated recon agent from accidentally firing exploits when it detects a vulnerability during scanning.

**Delegation example:**
```json
{
  "tool_name": "call_subordinate",
  "tool_args": {
    "message": "Enumerate all services on 10.10.10.5, map web directories, and return a structured port scan + web fingerprint summary.",
    "agent_profile": "recon"
  }
}
```

---

## exploit-dev

**Location:** `agents/exploit-dev/`

Exploit research, adaptation, and payload generation specialist.

**Files:**
- `agent.json` — `"title": "Exploit Developer"`
- `prompts/agent.system.main.role.md` — Exploit research (searchsploit, GitHub, Metasploit source), msfvenom payload generation for all platforms (ELF, EXE, DLL, PS1, HTA, WAR, JSP, PHP, Android APK), encoding for AV evasion, template injection, custom exploit development (buffer overflow, format string, web exploits, impacket scripts). Standardized exploit delivery output format.
- `prompts/agent.system.main.communication.md` — Complete working code only (no scaffolds), failure protocol, security annotations (stability risk, noise level, cleanup).

**Delegation example:**
```json
{
  "tool_name": "call_subordinate",
  "tool_args": {
    "message": "Target: Apache 2.4.49 on 10.10.10.5:80 (Linux x64). CVE-2021-41773 confirmed. Deliver a working reverse shell payload with execution steps. LHOST=10.10.14.2 LPORT=4444.",
    "agent_profile": "exploit-dev"
  }
}
```

---

## reporter

**Location:** `agents/reporter/`

Professional pentest report generation from structured findings data.

**Files:**
- `agent.json` — `"title": "Security Reporter"`
- `prompts/agent.system.main.role.md` — Full report structure: Cover Page, Executive Summary, Scope & Methodology, Risk Rating Matrix, Findings (CVSS-sorted), Appendix. CVSS 3.1 scoring guidance. Output in Markdown, HTML (CSS-styled), or PDF (weasyprint). Explicit constraint: "never fabricate findings".
- `prompts/agent.system.main.communication.md` — Tone guidance (executive vs technical), formatting rules, completeness checklist.

**Delegation example:**
```json
{
  "tool_name": "call_subordinate",
  "tool_args": {
    "message": "Generate a full HTML pentest report for engagement 'corp-external'. Client: Acme Corporation. Tester: Agent Zero Red Team. Load findings from the engagement workspace.",
    "agent_profile": "reporter"
  }
}
```

---

## default

**Location:** `agents/default/`

Minimal profile used as the fallback when no profile is specified. Contains only `agent.json` and `_context.md`. Inherits all global prompts without modification.

---

## _example

**Location:** `agents/_example/`

Template for creating new custom profiles. Contains:
- `prompts/agent.system.main.role.md` — skeleton role prompt
- `prompts/agent.system.tool.example_tool.md` — how to document a new tool
- `tools/example_tool.py` — minimal tool class
- `tools/response.py` — response tool override
- `extensions/agent_init/_10_example_extension.py` — minimal extension class

---

## Creating a Custom Profile

1. **Create the directory:**
```bash
mkdir -p agents/my-profile/prompts agents/my-profile/extensions
```

2. **Write `agent.json`:**
```json
{
  "title": "My Profile",
  "description": "What this agent does.",
  "context": "When to use this agent (shown in call_subordinate docs)."
}
```

3. **Override only what you need:**
```bash
# Copy and edit the role prompt
cp prompts/agent.system.main.role.md agents/my-profile/prompts/
# Edit to define the agent's identity and methodology
```

4. **Add custom tools** (if needed):
```bash
# See tools.md for the Tool base class
cp python/tools/search_engine.py python/tools/my_tool.py
# Edit, then add prompt docs:
cp prompts/agent.system.tool.search_engine.md agents/my-profile/prompts/agent.system.tool.my_tool.md
```

5. **Add custom extensions** (if needed):
```bash
# See extensions.md for the Extension base class
mkdir agents/my-profile/extensions/tool_execute_before
# Create _10_my_extension.py following the Extension pattern
```

6. **Add profile settings** (if needed):
```json
// agents/my-profile/settings.json
{
  "agent_memory_subdir": "my-profile"
}
```
