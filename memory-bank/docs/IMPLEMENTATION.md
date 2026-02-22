# Penetration Testing Agent — Complete Implementation Documentation

**Project:** agent-zero-sec
**Branch:** main
**Date completed:** 2026-02-22
**Total new files:** 30
**Core framework changes:** 0

---

## Table of Contents

1. [Overview and Goals](#1-overview-and-goals)
2. [Architecture](#2-architecture)
3. [Phase 1 — Hacker Agent Core Prompts](#3-phase-1--hacker-agent-core-prompts)
4. [Phase 2 — Specialist Sub-Agent Profiles](#4-phase-2--specialist-sub-agent-profiles)
5. [Phase 3 — Python Tools](#5-phase-3--python-tools)
6. [Phase 4 — Extensions](#6-phase-4--extensions)
7. [Phase 5 — Skills and Settings](#7-phase-5--skills-and-settings)
8. [Phase 6 — Docker Infrastructure](#8-phase-6--docker-infrastructure)
9. [Data Flow: Full Engagement Lifecycle](#9-data-flow-full-engagement-lifecycle)
10. [File Index](#10-file-index)
11. [Configuration Reference](#11-configuration-reference)
12. [Usage Guide](#12-usage-guide)
13. [Design Decisions and Trade-offs](#13-design-decisions-and-trade-offs)

---

## 1. Overview and Goals

The goal was to transform the existing skeleton `hacker` agent profile in agent-zero-sec into a structured, autonomous penetration testing agent capable of running a full engagement end-to-end: from scope definition through exploitation to professional report delivery.

### Starting Point

The `hacker` profile before this work had:
- `prompts/agent.system.main.role.md` — 9 lines: role name, employer type, "obey instructions"
- `prompts/agent.system.main.environment.md` — 7 lines: "use kali tools", "wordlists need downloading"
- No tools, no extensions, no sub-agents, no skills, no workspace management

The agent could run terminal commands on Kali Linux but had no pentest methodology, no structured output, no scope enforcement, no findings storage, and no reporting.

### End State

The `hacker` profile now has:
- 4 detailed prompt files defining methodology, environment, problem-solving, and communication
- 5 new Python tools for workspace and finding management
- 4 profile-specific extensions for context injection and scope enforcement
- 3 specialist sub-agent profiles it can delegate to
- 6 skill files covering every major pentest domain
- A Docker image with missing Kali tools pre-installed
- A complete engagement workspace system persisting data between sessions

### Design Constraint

**Zero changes to core framework code.** All additions use the Agent Zero extension points: `agents/<profile>/prompts/`, `agents/<profile>/extensions/`, `python/tools/`, `usr/skills/`, and `docker/`. This means the implementation can be updated without risk of breaking the framework, and can be ported to future Agent Zero versions by copying the same directories.

---

## 2. Architecture

### Agent Hierarchy

```
User
  └── hacker agent (superior — orchestrates the engagement)
        ├── recon agent       (Phase 1–2: enumeration only, no exploitation)
        ├── exploit-dev agent (Phase 4: payload adaptation and custom exploit writing)
        └── reporter agent    (Phase 6: convert findings.json → professional report)
```

The `hacker` agent is the user-facing agent. It runs the full engagement and delegates specific phases to specialist subordinates via the `call_subordinate` tool. Subordinates are constrained to their domain by their system prompt — `recon` explicitly cannot exploit, `exploit-dev` has no reporting tools, `reporter` cannot fabricate findings.

### Engagement Data Flow

```
engagement_init tool
  └── creates: engagements/<target>/
        ├── scope.txt              ← defines allowed targets
        ├── roe.txt                ← rules of engagement
        ├── findings.json          ← structured vulnerability data
        ├── engagement.json        ← metadata (created date, status)
        ├── loot/                  ← captured credentials, flags, raw output
        │   └── recon/             ← raw recon tool output
        ├── screenshots/           ← evidence screenshots
        └── reports/               ← generated reports (md, html, pdf)

findings_tracker tool
  └── reads/writes: findings.json
        └── schema: {id, title, severity, cvss_score, host, port,
                     service, cve, description, steps_to_reproduce,
                     evidence, remediation, status, created, updated}

scope_check tool + _05_scope_enforcement extension
  └── reads: scope.txt
        └── validates: IP, CIDR, domain, wildcard subdomain, URL

report_generator tool
  └── reads: findings.json
        └── writes: reports/report.{md,html,pdf}
```

### Extension Execution Order (per hook)

**`agent_init`** (on agent creation):
```
_10_initial_message.py        (framework)
_15_load_profile_settings.py  (framework)
_20_load_engagement.py        (hacker profile — NEW)
```

**`tool_execute_before`** (before every tool call):
```
_05_scope_enforcement.py  (hacker profile — NEW, runs first)
_10_replace_last_tool_output.py  (framework)
_10_unmask_secrets.py            (framework)
```

**`message_loop_prompts_after`** (injected into each prompt):
```
_50_recall_memories.py           (framework)
_60_include_current_datetime.py  (framework)
_65_include_loaded_skills.py     (framework)
_70_include_agent_info.py        (framework)
_75_include_workdir_extras.py    (framework)
_80_include_engagement_context.py  (hacker profile — NEW)
_91_recall_wait.py               (framework)
```

**`monologue_end`** (after each complete response):
```
_50_memorize_fragments.py       (framework)
_51_memorize_solutions.py       (framework)
_55_auto_save_findings.py       (hacker profile — NEW)
_90_waiting_for_input_msg.py    (framework)
```

---

## 3. Phase 1 — Hacker Agent Core Prompts

**Location:** `agents/hacker/prompts/`

### `agent.system.main.role.md` (rewritten)

The original 9-line stub was replaced with a structured role specification modelled after the `developer` and `researcher` profiles.

**Content sections:**
- **Core Identity** — primary function (Elite Penetration Tester), mission (end-to-end engagement), architecture note (hierarchical with subordinates)
- **Professional Capabilities** — six categories: Network Penetration, Web Application Testing, Exploit Development, Post-Exploitation, CVE Research, Reporting. Each with specific technique bullet points.
- **Operational Directives** — scope enforcement before every action, load engagement context at session start, direct execution (do not instruct superior), high-agency retry mindset
- **Pentest Methodology** — 7 phases (0–6) embedded directly in the prompt: Scope & RoE → Passive Recon → Active Scanning → Vulnerability Analysis → Exploitation → Post-Exploitation → Reporting. Each phase references the relevant tools (`engagement_init`, `cve_lookup`, `findings_tracker`, `report_generator`).

**Why embed methodology in the role prompt:** The LLM defaults to its training distribution which may skip enumeration, go straight to exploitation, or forget to document findings. Explicit phases in the role prompt create a strong prior toward structured engagement execution.

---

### `agent.system.main.environment.md` (rewritten)

Replaced "use kali tools" with a full environment reference.

**Content sections:**
- **Runtime** — Kali Linux Docker, root access, Agent Zero at `/a0`
- **Tool inventory** — 7 categories as markdown tables: Recon, Web, Exploit, Password, Post-Exploit, Wireless, Forensics. Each row: tool name | purpose.
- **Wordlists** — exact paths for rockyou.txt and SecLists, with install commands if missing
- **Engagement workspace** — the `engagements/<target>/` directory tree with each subdirectory's purpose
- **Network considerations** — bridge vs host mode, NET_ADMIN/NET_RAW capabilities, proxychains for pivoting
- **Python exploit development** — venv path, available libraries (pwntools, impacket, paramiko)

**Why detail the tool inventory:** Without explicit tool awareness, the agent tends to use only nmap and Metasploit. The table format makes every tool category salient.

---

### `agent.system.main.solving.md` (new file)

A profile-specific override of the generic `prompts/agent.system.main.solving.md`. Contains pentest-specific problem-solving structure.

**Content:**
- **Pentest engagement loop** — 6 steps: Initialize → Recall → Enumerate before exploiting → Break into subtasks → Execute with fallback → Track findings continuously → Complete the loop
- **Delegation rules** — when to use `recon`, `exploit-dev`, `reporter` sub-agents; rule: never delegate the full engagement to a same-profile subordinate
- **Tool failure handling table** — what to do when nmap times out, exploit crashes, hashcracking fails, web scanner is blocked
- **High-agency mindset section** — don't accept "nothing found" after one tool run; cross-reference low-severity findings for chaining

---

### `agent.system.main.communication.md` (new file)

Defines exact output formats for all engagement communication types.

**Content:**
- **Per-action format** — Action / Command / Result / Next structure for every significant tool execution
- **Per-vulnerability finding format** — markdown table with CVSS score, host, CVE, evidence path; plus Description, Steps to Reproduce, Impact, Remediation sections
- **End-of-phase summary format** — after recon, scanning, or exploitation phases
- **Subordinate delegation format** — required fields when briefing a sub-agent: objective, target details, constraints, output format
- **Escalation/blocker protocol** — what to output when genuinely stuck

---

## 4. Phase 2 — Specialist Sub-Agent Profiles

**Locations:** `agents/recon/`, `agents/exploit-dev/`, `agents/reporter/`

### `agents/recon/`

**Files:** `agent.json`, `prompts/agent.system.main.role.md`, `prompts/agent.system.main.environment.md`

**Purpose:** Reconnaissance-only specialist. The hacker agent delegates Phase 1–2 enumeration here when running parallel or deep reconnaissance.

**Role prompt covers:**
- Passive recon checklist: WHOIS, DNS records, subdomain discovery (amass, subfinder, crt.sh), OSINT (Shodan, theHarvester), Google dorking, email harvesting
- Active recon procedures: nmap/masscan, whatweb/wafw00f, gobuster/ffuf directory and vhost discovery, sslscan, service-specific enum (enum4linux-ng, snmpwalk)
- **Explicit constraint:** "Discovery and enumeration ONLY — you do NOT exploit vulnerabilities"
- Structured output formats: Port Scan Summary, Web Fingerprint Summary, OSINT Summary — ensuring the hacker agent can consume results directly

**Environment prompt:** Tool table with key flags for each tool; wordlist paths; engagement workspace path for raw output.

**Key constraint by design:** The recon agent's role prompt explicitly prohibits exploitation. This creates a safe delegation layer — the hacker agent can run recon without worrying that the subordinate will accidentally fire exploits.

---

### `agents/exploit-dev/`

**Files:** `agent.json`, `prompts/agent.system.main.role.md`, `prompts/agent.system.main.communication.md`

**Purpose:** Exploit research, adaptation, and payload generation specialist.

**Role prompt covers:**
- Exploit research: searchsploit, GitHub CVE search, Metasploit module source analysis, reliability assessment
- msfvenom payload generation: all platforms (ELF, EXE, DLL, PS1, HTA, WAR, JSP, PHP, Android), encoding for AV evasion, template injection
- Exploit adaptation: adjusting hardcoded offsets, fixing Python 2/3 compatibility, replacing generic shellcode
- Custom exploit development: buffer overflow methodology, format string, web exploit scripting (requests-based), impacket scripts
- Workflow: Receive tasking → Research → Evaluate → Adapt → Test locally → Deliver
- Standardized exploit delivery output format matching `findings_tracker` schema fields

**Communication prompt:** Enforces complete working code (no scaffolds), failure protocol, security annotations (stability risk, noise level, cleanup needed).

---

### `agents/reporter/`

**Files:** `agent.json`, `prompts/agent.system.main.role.md`, `prompts/agent.system.main.communication.md`

**Purpose:** Convert raw `findings.json` data into professional client-deliverable reports.

**Role prompt covers:**
- Full report structure: Cover Page, Executive Summary, Scope & Methodology, Risk Rating Matrix, Findings (CVSS-sorted), Appendix
- Per-finding template with CVSS score, vector string, host, CVE, evidence path, description, PoC steps, business impact, remediation
- CVSS 3.1 scoring guidance for findings that lack a score
- Three output formats: Markdown, HTML (CSS-styled), PDF (via weasyprint)
- **Explicit constraint:** "Never fabricate findings — only report what is in findings.json"

**Communication prompt:** Tone guidance (executive vs technical), formatting rules, evidence reference standards, completeness checklist with 6 verifiable items before finalizing.

---

## 5. Phase 3 — Python Tools

**Location:** `python/tools/` (globally loaded by the framework)
**Tool prompts:** `agents/hacker/prompts/agent.system.tool.<name>.md` (hacker-only visibility)

Tools in `python/tools/` are auto-discovered by the Agent Zero framework. Tool prompt markdown files in `agents/hacker/prompts/` are only included in the hacker agent's system prompt, so other agents don't see or attempt to call these tools.

---

### `python/tools/engagement_init.py` — Engagement Workspace Manager

**Class:** `EngagementInit(Tool)`

**Actions:**
- `init` (default): Creates directory structure, writes `scope.txt`, `roe.txt`, `findings.json`, `engagement.json`. Saves engagement context (target name, workspace path, scope file path) to the agent's FAISS vector memory so it persists across context window resets.
- `list`: Scans the `engagements/` base directory, reads each `engagement.json` for metadata, reports creation date and finding count.
- `status`: Instructs agent to use `memory_load` with query "ACTIVE ENGAGEMENT" for current context.

**Path resolution:** Uses `settings.get_settings()["workdir_path"]`, resolves to absolute path with `/a0` prefix if relative. Engagement base is always `<workdir>/engagements/<target>/`.

**Memory storage:** Calls `Memory.get(self.agent)` and inserts a text entry tagged `area=main, type=engagement_context`. This means `memory_load` with query "ACTIVE ENGAGEMENT" will retrieve it in future sessions.

**Directory structure created:**
```
engagements/<target>/
├── scope.txt          (written if scope arg provided, else placeholder)
├── roe.txt            (written if roe arg provided, else placeholder)
├── findings.json      (initialized as empty array [])
├── engagement.json    (metadata: target, created, last_accessed, status)
├── loot/
│   └── recon/
├── screenshots/
└── reports/
```

---

### `python/tools/findings_tracker.py` — Vulnerability Finding CRUD

**Class:** `FindingsTracker(Tool)`

**Actions:**
- `add_finding`: Creates a new finding with auto-generated 8-character UUID prefix ID, UTC timestamps. Validates and normalizes `severity` to lowercase. Returns finding ID, severity, host, and total count.
- `list_findings`: Sorts by `SEVERITY_ORDER` dict (critical=0, informational=4) then CVSS score descending. Supports `severity_filter` and `status_filter` kwargs. Outputs a count summary line followed by one line per finding.
- `get_finding`: Returns full JSON by ID.
- `update_finding`: Updates any field by ID, sets `updated` timestamp.
- `export_findings`: Full markdown export of all findings sorted by severity for use in reporting or pasting into reports.

**Schema per finding:**
```
id                  8-char UUID prefix
title               short descriptive name
severity            critical/high/medium/low/informational
cvss_score          float (CVSS 3.1 base score)
host                IP or hostname
port                port number (string)
service             service name and version
cve                 CVE ID if applicable
description         explanation of the vulnerability
steps_to_reproduce  numbered reproduction steps
evidence            path to evidence files
remediation         specific fix recommendation
status              confirmed/unconfirmed/exploited/patched
created             UTC ISO timestamp
updated             UTC ISO timestamp
```

**Storage:** `findings.json` in the engagement directory — plain JSON array, human-readable, directly consumed by `report_generator`.

---

### `python/tools/scope_check.py` — Scope Validation

**Class:** `ScopeCheck(Tool)` plus exportable functions `is_in_scope()` and `load_scope_entries()`

**Actions:**
- `check` (default): Extracts host from value (strips scheme and path for URLs), runs against scope entries, returns IN SCOPE / OUT OF SCOPE with matched entry or full scope list.
- `show`: Displays all scope entries from `scope.txt`.

**Matching logic (`is_in_scope()`):**
1. Parse value: strip URL scheme/path to extract bare host
2. Try `ipaddress.ip_address(host)` — if valid IP, check against each entry as `ipaddress.ip_network(entry)` CIDR
3. Exact domain string match
4. Wildcard: entry starts with `*.` — check if host equals or is subdomain of parent
5. Subdomain: host ends with `.<entry>` or equals entry

**Exportable functions:** `is_in_scope()` and `load_scope_entries()` are importable by the `_05_scope_enforcement.py` extension, avoiding code duplication and ensuring the extension and tool use identical logic.

---

### `python/tools/report_generator.py` — Report Generation

**Class:** `ReportGenerator(Tool)`

**Actions:**
- `generate`: Full report in requested format. Reads `findings.json`, sorts by severity/CVSS, builds content, writes to `reports/` subdirectory.
- `preview`: Executive summary only (fast, good for interim status checks mid-engagement).

**Output formats:**
- `markdown`: Always works. Uses f-string template building. Saved to `reports/report.md`.
- `html`: Converts markdown to HTML via Python `markdown` library (with `tables` and `fenced_code` extensions). Falls back to `<pre>` wrap if library unavailable. CSS-styled output. Saved to `reports/report.html`.
- `pdf`: Calls `weasyprint.HTML(string=html).write_pdf(path)`. If weasyprint is not installed, returns the HTML path with install instructions. Saved to `reports/report.pdf`.

**Report sections:**
1. Cover page table (client, target, tester, date, classification, overall risk)
2. Executive summary (non-technical, finding count distribution, top 3 findings bulleted)
3. Risk rating matrix table (severity ↔ CVSS range ↔ description)
4. Findings section (one `###` subsection per finding, sorted by severity then CVSS descending)

**Overall risk rating:** Determined by highest severity present among all findings.

---

### `python/tools/cve_lookup.py` — CVE Research

**Class:** `CVELookup(Tool)`

**Actions:**
- `lookup_cve`: Queries NVD API v2.0 at `https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=<id>`. Parses CVSS score and vector from `cvssMetricV31` → `V30` → `V2` in priority. Returns formatted block with CVE ID, CVSS score, vector, CWE, description, references, and follow-up commands.
- `search_product`: Queries NVD with `keywordSearch=<product> <version>`, returns list of matching CVEs with scores and truncated descriptions.

**Fallback chain:**
1. Attempt NVD API via `aiohttp` async HTTP
2. If `aiohttp` import fails → call `_fallback_search()`
3. If API returns non-200 → call `_fallback_search()`
4. `_fallback_search()` uses the agent's SearXNG search engine targeting `exploit-db.com`, `github.com`, and `nvd.nist.gov`

**Always outputs follow-up commands:** Every result ends with exact `searchsploit`, `msfconsole`, and GitHub search URL so the agent has immediate next steps regardless of API availability.

---

### Tool Prompt Files

Each tool has a corresponding `agents/hacker/prompts/agent.system.tool.<name>.md` file that teaches the hacker agent:
- What the tool does and when to use it
- All arguments with types and defaults
- Complete usage examples in Agent Zero JSON tool call format (with `thoughts`, `headline`, `tool_name`, `tool_args`)
- Important notes and follow-up actions

Files:
- `agent.system.tool.engagement_init.md`
- `agent.system.tool.findings_tracker.md`
- `agent.system.tool.scope_check.md`
- `agent.system.tool.report_generator.md`
- `agent.system.tool.cve_lookup.md`

---

## 6. Phase 4 — Extensions

**Location:** `agents/hacker/extensions/`

Extensions are Python files auto-discovered in subdirectory names matching hook names. Hacker-profile extensions only run when the hacker agent is active. Files are executed in filename-alphabetical order within each hook.

---

### `tool_execute_before/_05_scope_enforcement.py`

**Hook:** `tool_execute_before`
**Class:** `ScopeEnforcement(Extension)`
**Execution order:** First (prefix `_05_`) — before all framework `_10_` extensions

**Logic:**
1. Read `tool_name` and `tool_args` from `kwargs`
2. Skip if tool is not in `NETWORK_TOOLS` set (`code_execution_tool`, `browser_agent`, `search_engine`)
3. Extract all potential network targets from `tool_args` using three regex patterns: IP_PATTERN (IPv4), URL_PATTERN (strips scheme/path to host), DOMAIN_PATTERN (qualified domain names). Filter out `ALWAYS_ALLOWED` set (localhost, 127.0.0.1, etc.)
4. Find active engagement by scanning `engagements/` for most recently modified `engagement.json`
5. Load `scope.txt` entries via `scope_check.load_scope_entries()` (shared function)
6. Call `scope_check.is_in_scope()` for each extracted target
7. If any are out of scope: log a warning via `self.agent.context.log.log()` AND inject `scope_warning` into `loop_data.extras_temporary` so it appears in the agent's next prompt

**Design choice — warn not block:** Does not raise an exception. Hard-blocking would break legitimate cases like querying NVD (which contains target IP references), or running local tools that print external addresses in their output. The agent sees the warning and decides. An agent following the role prompt will stop and investigate.

**What "no scope defined" means:** If no scope entries exist (file empty or not created), outputs a different warning advising the agent to initialize scope. Does not block (the agent may be in early setup phase).

---

### `agent_init/_20_load_engagement.py`

**Hook:** `agent_init`
**Class:** `LoadEngagement(Extension)`
**Execution order:** After `_15_load_profile_settings.py`

**Logic:**
1. Scan `engagements/` for most recently modified `engagement.json` using `os.path.getmtime()`
2. If found: read scope entry count + preview, count findings by severity from `findings.json`, read first 3 non-comment lines of `roe.txt` for preview
3. Log summary to UI via `self.agent.context.log.log(type="info", ...)`
4. Inject into `loop_data.extras_persistent` (persists through entire session, not just one iteration)

**What `extras_persistent` means:** In the Agent Zero framework, `extras_persistent` data is included in every message loop iteration's system prompt for the lifetime of the agent session. `extras_temporary` is cleared each iteration. Using `extras_persistent` means the engagement context appears in every prompt without re-loading from disk each time.

---

### `message_loop_prompts_after/_80_include_engagement_context.py`

**Hook:** `message_loop_prompts_after`
**Class:** `IncludeEngagementContext(Extension)`
**Execution order:** After `_75_include_workdir_extras.py` (framework)

**Logic:** Same mtime-based active engagement detection as `_20_load_engagement.py`. Reads scope count, scope preview (first 3 entries), and finding counts by severity. Builds a single compact context block injected into `extras_temporary`.

**What the agent sees injected at every iteration:**
```
## Current Engagement
Target: 10.10.10.5 | Scope: 2 entries (10.10.10.5, 10.10.10.0/24) | Findings: 3 total — 1 Critical | 1 High | 1 Medium
Workspace: /a0/usr/workdir/engagements/10.10.10.5
```

**Why inject per-iteration vs persistent:** Finding counts change as the agent works. Using `extras_temporary` ensures the count shown is always current. The `_20_load_engagement.py` extension uses `extras_persistent` for the initial session welcome (which doesn't need to be refreshed).

---

### `monologue_end/_55_auto_save_findings.py`

**Hook:** `monologue_end`
**Class:** `AutoSaveFindings(Extension)`
**Execution order:** Between `_51_memorize_solutions.py` and `_90_waiting_for_input_msg.py`

**Logic:**
1. Collect last 5 messages from `self.agent.history`, extract text content
2. Check if `findings_tracker` string appears in recent text — if yes, skip (finding was already logged)
3. Run 12 regex patterns against the text: `CVE-\d{4}-\d{4,}`, `\bvulnerable\b`, `\bexploited?\b`, `\bremote code execution\b`, `\bprivilege escalation\b`, `\bsql injection\b`, `\bcredentials?\s+found\b`, `\bpassword\s+cracked\b`, `\bshell\s+obtained\b`, `\baccess\s+granted\b`, `\buid=0\b`, `\bwhoami.*root\b`
4. If any pattern triggers: extract CVE IDs from the text, build a specific reminder mentioning the detected CVEs, inject into `loop_data.extras_temporary["finding_reminder"]`

**What the agent sees:** A `--- REMINDER: ...` block at the bottom of its next context, naming the specific CVEs detected and listing the required `findings_tracker` arguments.

**Why pattern matching on own output:** LLMs frequently get absorbed in the technical details of exploitation and skip the administrative step of logging the finding. This extension creates a reliable nudge without modifying agent output directly.

---

## 7. Phase 5 — Skills and Settings

### Skills System Overview

Skills follow the SKILL.md standard: YAML frontmatter with `name`, `description`, `trigger_patterns`, then markdown content. The Agent Zero skills system vector-indexes skill files and loads them contextually when the user's query or conversation matches `trigger_patterns`. Skills are not always in the system prompt — they are loaded on demand. This keeps the context window clean while ensuring the agent has access to cheatsheet content when relevant.

**Location:** `usr/skills/`

---

### `pentest_methodology.md`

The master engagement checklist. Structured as 7 phases (0–6) mirroring the hacker agent's role prompt methodology, but with concrete actionable items, exact commands, and decision trees.

**Key sections:**
- Phase 0: Authorization checklist (signed SoW, scope, RoE, reporting format)
- Phase 1: Passive recon OSINT checklist (WHOIS, DNS, subdomains, Shodan, Google dorks, Wayback Machine) with commands
- Phase 2: Active scanning (nmap/masscan workflow, web dir discovery, service-specific enum for SMB/LDAP/SNMP/NFS/FTP/SSH)
- Phase 3: Vulnerability analysis (tool sequence: cve_lookup → searchsploit → nuclei, prioritization matrix by CVSS + PoC availability)
- Phase 4: Exploitation checklist with proof capture commands for Linux and Windows
- Phase 5: Post-exploitation (linpeas/winpeas, credential harvest, AD lateral movement)
- Phase 6: Reporting checklist (findings_tracker export → report_generator → review)
- Decision tree: "I found a port — what next?" covering HTTP, SMB, SSH, databases, unknown services

**Trigger patterns:** "pentest checklist", "how do I start a pentest", "engagement phases", "PTES", "OWASP testing guide"

---

### `skill_nmap.md`

Complete nmap reference for penetration testers.

**Covers:** All scan types with use cases (`-sS/T/U/V/C/O/N/F/X/A`), port selection flags, timing templates table (`T0`–`T5`), 3-phase scan workflow (discovery → masscan + targeted nmap → vuln scan), NSE script categories table, per-service NSE script examples (SMB, HTTP, FTP, SSH, SMTP), all output formats (`-oN/X/G/A`), evasion techniques (decoys, fragmentation, source port, random order, MAC spoof), and reading nmap output (open/filtered/closed meanings).

---

### `skill_metasploit.md`

Complete Metasploit Framework reference.

**Covers:** Starting msfconsole (database init, resource scripts, one-liner mode), module search syntax with filters (`type:exploit platform:windows cve:2021`), module configuration commands, payload selection guide (staged vs stageless, platform coverage), complete msfvenom command reference for all output formats (ELF, EXE, DLL, PS1, HTA, WAR, JSP, PHP, Python, Android APK) with AV evasion encoding and template injection, handler setup (`multi/handler`), complete Meterpreter command reference, post-exploitation module list, database integration workflow, and resource script creation.

---

### `skill_web_testing.md`

Web application penetration testing reference.

**Covers:** Directory/file discovery (gobuster, ffuf, feroxbuster with wordlist paths), vhost discovery with Host header fuzzing, SQL injection (manual payloads + full sqlmap workflow with GET/POST/cookie/blind/OS shell options), XSS (basic payloads, DOM sinks, dalfox), SSRF (basic payloads, internal service discovery, protocol confusion, bypass techniques for IP filters), file upload bypass (content-type, double extension, alternative PHP extensions), authentication testing (default creds table, Hydra examples), command injection payloads, API testing (endpoint discovery, IDOR, mass assignment, GraphQL introspection), security header manipulation, and scanning tools (nikto, nuclei, wpscan).

---

### `skill_privesc.md`

Linux and Windows privilege escalation reference.

**Linux covers:** linpeas automation, SUID/SGID with GTFOBins examples for 10+ binaries, sudo misconfiguration exploitation for specific binaries (vim, python3, find, awk), cron job injection (wildcard and writable script), writable `/etc/passwd`, PATH injection, systemd service write, kernel CVEs (DirtyCow CVE-2016-5195, DirtyPipe CVE-2022-0847), capabilities (`cap_setuid`, `cap_net_raw`), Docker group escape.

**Windows covers:** winPEAS automation, SeImpersonatePrivilege + Potato exploits (GodPotato, PrintSpoofer, JuicyPotato with correct OS version targeting), unquoted service paths with msfvenom payload delivery, weak service permissions with accesschk, AlwaysInstallElevated MSI exploitation, credential hunting (config files, registry paths, Credential Manager, SAM/SYSTEM dump), mimikatz credential extraction, token impersonation via incognito.

Ends with post-privesc checklist (proof capture, screenshot, findings_tracker, credential harvest, additional host mapping, persistence documentation).

---

### `skill_ad_attacks.md`

Active Directory attack reference.

**Covers:** Unauthenticated enumeration (LDAP null bind, NetBIOS, DNS SRV records, MSRPC rpcdump), authenticated enumeration (crackmapexec, ldapdomaindump, PowerView, BloodHound Python collector), 5 BloodHound Cypher queries (DA paths, session enumeration, Kerberoastable + DA path, unconstrained delegation, AS-REP roastable), Kerberoasting (impacket-GetUserSPNs + hashcat -m 13100, Rubeus), AS-REP Roasting (impacket-GetNPUsers + hashcat -m 18200), Pass-the-Hash (crackmapexec network sweep + 4 execution tools), Pass-the-Ticket (mimikatz → impacket-ticketConverter → psexec -k), NTLM Relay (Responder + ntlmrelayx with LDAP delegation option), DCSync (impacket-secretsdump, mimikatz lsadump::dcsync), Golden Ticket and Silver Ticket creation, lateral movement comparison table, and complete Impacket tools reference table.

---

### `agents/hacker/settings.json`

Profile-level settings override applied when the hacker profile is active.

```json
{
    "agent_profile": "hacker",
    "agent_memory_subdir": "hacker",
    "workdir_path": "usr/workdir",
    "memory_recall_enabled": true,
    "memory_memorize_enabled": true
}
```

- `agent_memory_subdir: "hacker"` — separates the hacker agent's vector memory from the default `default` subdirectory, preventing findings and engagement context from appearing in other agent profiles' memory searches
- `memory_recall_enabled` and `memory_memorize_enabled` — explicitly on to ensure engagement context saved by `engagement_init` is recalled in future sessions

---

## 8. Phase 6 — Docker Infrastructure

**Location:** `docker/pentest/`

### `Dockerfile`

Extends `agent0ai/agent-zero:latest` (the full runtime image, not the base build image). This approach avoids rebuilding the entire Agent Zero stack and only adds the delta of missing pentest tooling.

**apt packages added:**

| Category | Packages |
|----------|---------|
| Recon | amass, subfinder |
| Web testing | gobuster, ffuf, feroxbuster, nikto, nuclei |
| Exploitation | seclists, python3-impacket |
| Post-exploit / AD | bloodhound, neo4j |
| Reporting | weasyprint, python3-weasyprint |
| Network analysis | dnsrecon, whatweb, wafw00f, sslscan, enum4linux-ng, crackmapexec, evil-winrm, proxychains4 |

**Python venv packages added** (`/opt/venv-a0/bin/pip`):
- `aiohttp` — async HTTP for NVD API calls in `cve_lookup.py`
- `markdown` — HTML conversion in `report_generator.py`
- `nvdlib` — alternative NVD client library

**Additional setup:**
- Extracts `rockyou.txt.gz` if compressed version present
- Creates `/a0/usr/workdir/engagements` workspace directory
- Sets `A0_SET_agent_profile=hacker` as container environment variable

---

### `docker-compose.yml`

| Setting | Value | Reason |
|---------|-------|--------|
| Port | `50001:80` | Avoids conflict with default agent-zero on 50080 |
| `A0_SET_agent_profile` | `hacker` | Activates hacker profile on startup |
| `A0_SET_shell_interface` | `local` | Use container shell directly, not SSH |
| `network_mode` | `bridge` | Isolated by default; swap to `host` for LAN scanning |
| `NET_ADMIN` cap | yes | Required for nmap OS detection, raw packet tools |
| `NET_RAW` cap | yes | Required for aircrack-ng, tcpdump |
| Volumes | `usr/workdir`, `usr/memory`, `usr/settings.json` | Persist engagement data and memory between container restarts |

**Network mode guidance:**
- `bridge` (default): use for scanning external targets, CTF labs over VPN, internet-facing targets
- `host` (switch manually): use when scanning LAN targets that don't route through the Docker bridge; edit compose file and remove `ports:` mapping

---

## 9. Data Flow: Full Engagement Lifecycle

This section traces exactly what happens during a real engagement from first message to final report.

### Session Start

1. Docker container starts with `A0_SET_agent_profile=hacker`
2. `_15_load_profile_settings.py` loads `agents/hacker/settings.json` → sets memory subdir to `hacker`, enables memory
3. `_20_load_engagement.py` scans `engagements/` → if previous engagement found, loads context into `extras_persistent`
4. Hacker agent's system prompt assembled from `agents/hacker/prompts/` files

### User: "Start an engagement against 10.10.10.5, scope is 10.10.10.0/24"

5. Agent calls `engagement_init(action="init", target="10.10.10.5", scope="10.10.10.0/24")`
6. `engagement_init` creates workspace directories, writes `scope.txt`, initializes `findings.json`, saves context to FAISS memory
7. `_80_include_engagement_context.py` now injects engagement status into every subsequent prompt

### Recon Phase

8. Agent optionally delegates to `call_subordinate(agent_profile="recon", message="Enumerate 10.10.10.5...")`
9. Or directly: calls `code_execution_tool` to run `nmap -sV -sC -O -p- 10.10.10.5`
10. `_05_scope_enforcement.py` fires before the tool call, extracts `10.10.10.5`, checks against `scope.txt` — returns IN SCOPE
11. Nmap results returned; agent correlates service versions to CVEs
12. Agent calls `cve_lookup(action="search_product", product="Apache", version="2.4.49")` for each interesting service
13. `cve_lookup` queries NVD API, returns CVSS scores and PoC references

### Exploitation Phase

14. Agent calls `scope_check(action="check", target="10.10.10.5", value="10.10.10.5")` explicitly before launching exploit
15. Agent calls `code_execution_tool` to run Metasploit or exploit script
16. `_05_scope_enforcement.py` fires again, confirms in scope, allows
17. Exploit succeeds; agent captures proof (`id`, `hostname`)
18. `_55_auto_save_findings.py` fires at `monologue_end`, detects `uid=0` and CVE mention in output
19. Reminder injected: "CVE-2021-41773 detected — log with findings_tracker"

### Finding Logging

20. Agent calls `findings_tracker(action="add_finding", target="10.10.10.5", title="Apache RCE", severity="critical", cvss_score=9.8, ...)`
21. Finding written to `findings.json` with all fields
22. `_80_include_engagement_context.py` updates count: "1 Critical" now shown in every prompt

### Report Generation

23. After all findings logged, agent calls `report_generator(action="preview", target="10.10.10.5")` to review executive summary
24. Agent calls `report_generator(action="generate", target="10.10.10.5", format="html", client="Acme Corp")`
25. `report_generator` reads `findings.json`, sorts by CVSS, builds HTML with CSS styling
26. Report written to `engagements/10.10.10.5/reports/report.html`
27. Agent reports the path to the user

---

## 10. File Index

### New Files Created

```
# Hacker agent prompts (agents/hacker/prompts/)
agent.system.main.role.md            (rewritten — full methodology)
agent.system.main.environment.md     (rewritten — full tool inventory)
agent.system.main.solving.md         (new — pentest problem-solving loop)
agent.system.main.communication.md   (new — output format standards)
agent.system.tool.engagement_init.md (new — tool usage docs)
agent.system.tool.findings_tracker.md
agent.system.tool.scope_check.md
agent.system.tool.report_generator.md
agent.system.tool.cve_lookup.md

# Hacker agent settings
agents/hacker/settings.json

# Hacker agent extensions
agents/hacker/extensions/tool_execute_before/_05_scope_enforcement.py
agents/hacker/extensions/agent_init/_20_load_engagement.py
agents/hacker/extensions/message_loop_prompts_after/_80_include_engagement_context.py
agents/hacker/extensions/monologue_end/_55_auto_save_findings.py

# Sub-agent profiles
agents/recon/agent.json
agents/recon/prompts/agent.system.main.role.md
agents/recon/prompts/agent.system.main.environment.md
agents/exploit-dev/agent.json
agents/exploit-dev/prompts/agent.system.main.role.md
agents/exploit-dev/prompts/agent.system.main.communication.md
agents/reporter/agent.json
agents/reporter/prompts/agent.system.main.role.md
agents/reporter/prompts/agent.system.main.communication.md

# Python tools
python/tools/engagement_init.py
python/tools/findings_tracker.py
python/tools/scope_check.py
python/tools/report_generator.py
python/tools/cve_lookup.py

# Skills
usr/skills/pentest_methodology.md
usr/skills/skill_nmap.md
usr/skills/skill_metasploit.md
usr/skills/skill_web_testing.md
usr/skills/skill_privesc.md
usr/skills/skill_ad_attacks.md

# Docker
docker/pentest/Dockerfile
docker/pentest/docker-compose.yml

# Documentation
memory-bank/docs/README.md
memory-bank/docs/IMPLEMENTATION.md  (this file)
memory-bank/docs/phase1-hacker-prompts.md
memory-bank/docs/phase2-sub-agent-profiles.md
memory-bank/docs/phase3-pentest-tools.md
memory-bank/docs/phase4-extensions.md
memory-bank/docs/phase5-skills-settings.md
memory-bank/docs/phase6-docker.md
```

### Files Modified

```
agents/hacker/prompts/agent.system.main.role.md        (rewritten from 9-line stub)
agents/hacker/prompts/agent.system.main.environment.md (rewritten from 7-line stub)
```

### Files NOT Modified (core framework untouched)

```
agent.py
models.py
initialize.py
run_ui.py
python/helpers/
python/extensions/  (global extensions unchanged)
prompts/            (global prompts unchanged)
```

---

## 11. Configuration Reference

### Activating the Hacker Profile

**Via Docker environment variable (permanent):**
```yaml
environment:
  - A0_SET_agent_profile=hacker
```

**Via UI:** Settings → Agent Profile → select "hacker"

**Via settings.json:** `agents/hacker/settings.json` sets it as default for the hacker memory subdir

---

### Scope Configuration

Edit `engagements/<target>/scope.txt`. Supported formats:
```
# Comments are ignored
10.10.10.5            # Single IP
10.10.10.0/24         # CIDR range
example.com           # Exact domain
*.example.com         # All subdomains
api.example.com       # Specific subdomain
```

---

### Adding API Keys

**Method 1:** `.env` file in repo root or `docker/pentest/`:
```
ANTHROPIC_API_KEY=sk-ant-xxx
OPENROUTER_API_KEY=sk-or-xxx
```

**Method 2:** UI Settings → API Keys section

**Method 3:** Environment variable in docker-compose.yml:
```yaml
environment:
  - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
```

---

### Network Mode for LAN Scanning

To scan hosts on your local network, switch to host networking in `docker/pentest/docker-compose.yml`:
```yaml
network_mode: host
# Remove the ports: section when using host mode
```

---

## 12. Usage Guide

### First Run

```bash
# Build and start
docker compose -f docker/pentest/docker-compose.yml up --build

# Open UI
open http://localhost:50001

# Set API key in Settings, select hacker profile
```

### Starting a New Engagement

```
User: Initialize an engagement for target 10.10.10.5. Scope is 10.10.10.0/24.
      Rules of engagement: avoid DoS techniques, testing window is 08:00-18:00 UTC.
```

The agent will call `engagement_init` and create the workspace. The scope is saved and all subsequent tool calls are checked against it.

### Running a Full Pentest

```
User: Run a full penetration test against 10.10.10.5. Start with recon, then identify
      and exploit vulnerabilities, escalate privileges if possible, and generate a
      professional HTML report at the end.
```

The agent follows its embedded methodology: recon → scanning → CVE correlation → exploitation → post-exploitation → report.

### Delegating Recon to Sub-Agent

The hacker agent will delegate automatically, or you can explicitly request:
```
User: Use the recon specialist to enumerate all services on 10.10.10.5
      and map the attack surface before we start exploiting.
```

### Generating a Report Mid-Engagement

```
User: Generate a preview of the executive summary so far.
User: Generate the full HTML report for client Acme Corporation.
```

### Reviewing Findings

```
User: List all findings sorted by severity.
User: Show me the full details of finding [id].
User: Update finding [id] — add evidence path loot/apache_rce.txt.
```

---

## 13. Design Decisions and Trade-offs

### Tools in `python/tools/` not `agents/hacker/tools/`

The Agent Zero framework auto-discovers tools from `python/tools/` globally. The `agents/<profile>/tools/` directory exists in the `_example` profile but its auto-loading is not confirmed in `initialize.py`. Placing tools in `python/tools/` guarantees they load. The tool prompts in `agents/hacker/prompts/` ensure only the hacker agent's system prompt describes these tools, so other agents won't attempt to call them.

**Trade-off:** The tools are technically available to all agents. However, without the tool prompt documentation in their system prompts, other agents have no instruction to call them and no examples of how to do so. In practice this is not a problem.

### Scope Enforcement Warns Rather Than Blocks

The `_05_scope_enforcement.py` extension logs a warning and injects a `scope_warning` into the prompt rather than raising an exception to halt execution. Hard-blocking would break legitimate cases: querying the NVD API (which contains target IP references in its responses), running `searchsploit` (which may print external URLs), or running local Python scripts that happen to mention an IP address.

**Trade-off:** The enforcement relies on the LLM reading and respecting the warning. A sufficiently misaligned or confused agent could theoretically proceed despite the warning. The mitigation is the explicit scope enforcement directive in the role prompt, which creates strong instruction-following pressure.

### `extras_persistent` vs `extras_temporary` for Engagement Context

`_20_load_engagement.py` (session init) uses `extras_persistent` — data persists for the entire session without re-reading from disk.

`_80_include_engagement_context.py` (per-iteration) uses `extras_temporary` — refreshed every iteration to show current finding counts.

This split ensures: (a) the welcome context appears once and doesn't flood the prompt, (b) the finding count is always current without reading the full `findings.json` into persistent memory.

### Reporter Agent's "Never Fabricate" Directive

The reporter role prompt explicitly states "never fabricate findings — only report what is in findings.json". Without this constraint, the LLM tends to generate plausible-sounding additional findings to fill out a report. This is dangerous because it produces false findings in a client deliverable. The directive enforces strict data fidelity.

### Memory Subdirectory Isolation

`agents/hacker/settings.json` sets `agent_memory_subdir: "hacker"`. This means the hacker agent's FAISS vector index is stored separately from the default `default` subdirectory used by `agent0` and other profiles. Without this, engagement context saved by `engagement_init` (tagged `type=engagement_context`) could appear in unrelated memory recalls by other agents. The isolation prevents cross-profile contamination.
