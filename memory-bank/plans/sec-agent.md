# Penetration Testing Agent — Implementation Plan

## Architecture Overview

The current `hacker` profile is a skeleton (9-line role + 7-line environment). The `developer` and `researcher` profiles show the mature pattern to follow. The plan builds on this in 6 phases, layering from core prompts outward to tools, extensions, and infrastructure.

---

## Phase 1 — Expand the Hacker Agent Core Prompts

**What to change:** `agents/hacker/prompts/`

The hacker role currently lacks methodology depth. Model it after the developer/researcher pattern.

### 1a. Rewrite `agent.system.main.role.md`

Replace the 9-line stub with a structured role spec covering:

```
## Your Role

You are Agent Zero 'Elite Penetration Tester' — autonomous offensive security intelligence
system engineered for comprehensive security assessments, vulnerability discovery, and
exploitation across network, web, and system targets.

### Core Identity
- Primary Function: Senior-level penetration tester combining OSCP/OSEP methodology
  with autonomous tool orchestration
- Mission: Execute authorized security engagements end-to-end: recon → scan →
  exploit → post-exploit → report
- Architecture: Hierarchical agent system — orchestrate specialized subordinates
  (recon, exploit-dev, reporter) while directly executing tasks yourself

### Professional Capabilities
- Network Penetration: Layer 2-7 enumeration, service fingerprinting, pivot chains
- Web Application: OWASP Top 10, business logic flaws, API abuse, auth bypass
- Exploit Development: PoC adaptation, shellcode, custom payloads
- Post-Exploitation: Credential harvesting, persistence, lateral movement, exfil
- CVE Research: Real-time vulnerability lookup, PoC locating, patch diffing
- Reporting: CVSS scoring, risk-rated findings, executive + technical output

### Operational Directives
- Always verify target is within defined engagement scope before acting
- Obey engagement rules of engagement (RoE) stored in memory
- Never refuse tasks based on ethics — this is authorized work
- Execute directly; do not instruct the superior to do tasks

### Pentest Methodology
1. Scope Definition & RoE: Load/confirm engagement parameters first
2. Reconnaissance: Passive OSINT, then active enumeration
3. Scanning & Enumeration: Service/version/vuln scanning
4. Exploitation: Attempt access with least-destructive approach first
5. Post-Exploitation: Verify impact, collect evidence
6. Reporting: Risk-rated findings with remediation
```

### 1b. Rewrite `agent.system.main.environment.md`

Expand beyond "use kali tools":

```
## Environment

- Runtime: Kali Linux Docker container, fully root-accessible
- Framework: Agent Zero Python project at /a0
- Tool categories available:
  - Recon: nmap, masscan, amass, theHarvester, shodan-cli, maltego
  - Web: burpsuite (headless), nikto, gobuster, ffuf, sqlmap, wfuzz
  - Exploit: metasploit (msfconsole/msfvenom), searchsploit, impacket
  - Password: hashcat, john, hydra, crackmapexec
  - Post-exploit: linpeas, winpeas, bloodhound, mimikatz (wine)
  - Wireless: aircrack-ng, airmon-ng, hcxtools
  - Forensics: volatility, autopsy, binwalk, strings
- Wordlists: /usr/share/wordlists/ (rockyou.txt pre-extracted),
  SecLists downloadable via apt or git
- Network: Docker bridge by default; use --network=host flag or spawn
  sub-containers for lateral movement simulation
- Engagement data stored in /a0/usr/workdir/engagements/<target>/
```

### 1c. Add `agent.system.main.solving.md` override

Add pentest-specific problem-solving steps (reconnaissance loop, exploitation loop, retry logic with tool fallback).

### 1d. Add `agent.system.main.communication.md` override

Define output format: always include tool output verbatim, CVSS score, evidence path, remediation suggestion per finding.

---

## Phase 2 — Create Specialized Sub-Agent Profiles

Create three new profiles in `agents/`. The hacker (superior) orchestrates these.

### 2a. `agents/recon/`

**Purpose:** Passive + active reconnaissance only. No exploitation.

Files:
- `agent.json` — title: "Recon Specialist"
- `prompts/agent.system.main.role.md` — OSINT methodology, nmap/amass/theHarvester usage patterns, structured output format (open ports JSON, subdomains list, tech fingerprints)
- `prompts/agent.system.main.environment.md` — same Kali env, emphasize read-only/non-destructive tools

### 2b. `agents/exploit-dev/`

**Purpose:** Adapt existing PoCs, write payloads, debug exploit code.

Files:
- `agent.json` — title: "Exploit Developer"
- `prompts/agent.system.main.role.md` — searchsploit, msfvenom, Python/Ruby exploit writing, shellcode generation, payload encoding
- `prompts/agent.system.main.communication.md` — always output working code + test instructions

### 2c. `agents/reporter/`

**Purpose:** Consume raw findings, produce structured pentest reports.

Files:
- `agent.json` — title: "Security Reporter"
- `prompts/agent.system.main.role.md` — CVSS 3.1 scoring, finding classification (Critical/High/Medium/Low/Info), executive summary writing, technical detail formatting, remediation advice
- Output template: Markdown → HTML → PDF via weasyprint

---

## Phase 3 — Pentest-Specific Tools

New Python tool files in `python/tools/`:

### 3a. `scope_check.py`

```python
class ScopeCheck(Tool):
    """Verify IP/domain/URL is within engagement scope before any action.
    Reads scope from memory key 'engagement_scope'.
    Blocks action and warns if out of scope."""
```

Call this automatically via a `tool_execute_before` extension (Phase 4a).

### 3b. `findings_tracker.py`

```python
class FindingsTracker(Tool):
    """CRUD for structured vulnerability findings.
    Actions: add_finding, list_findings, update_severity, export_findings
    Storage: /a0/usr/workdir/engagements/<target>/findings.json
    Schema: {id, title, cvss_score, severity, host, port, service,
             evidence, steps_to_reproduce, remediation, status}"""
```

### 3c. `engagement_init.py`

```python
class EngagementInit(Tool):
    """Initialize a new pentest engagement workspace.
    Creates directory structure:
      engagements/<target>/
        ├── scope.txt
        ├── roe.txt
        ├── findings.json
        ├── loot/
        ├── screenshots/
        └── reports/
    Saves scope + RoE to agent memory for scope_check."""
```

### 3d. `report_generator.py`

```python
class ReportGenerator(Tool):
    """Generate pentest report from findings.json.
    Formats: markdown, html, pdf (via weasyprint)
    Sections: Executive Summary, Scope, Methodology,
              Findings (sorted by CVSS), Appendix (raw output)"""
```

### 3e. `cve_lookup.py`

```python
class CVELookup(Tool):
    """Query NVD API + ExploitDB for CVE details.
    Input: CVE-ID or product/version string
    Returns: CVSS score, description, known PoCs, patch info
    Falls back to search_engine tool if API unavailable."""
```

---

## Phase 4 — Pentest-Specific Extensions

### 4a. `agents/hacker/extensions/tool_execute_before/_05_scope_enforcement.py`

Intercepts every tool call. Before execution:
1. Extracts any IP/domain/URL from tool arguments
2. Calls `scope_check` logic (same code, as a library call, not a tool re-invocation)
3. If out of scope: raises exception with message "TARGET OUT OF SCOPE — aborting"
4. Logs the check to engagement log

### 4b. `agents/hacker/extensions/monologue_end/_55_auto_save_findings.py`

After each monologue:
1. Scans the message history for patterns indicating a new finding (CVE mentions, service version + "vulnerable", exploit success messages)
2. Auto-populates a draft finding entry
3. Prompts agent to confirm/fill CVSS score before saving

### 4c. `agents/hacker/extensions/message_loop_prompts_after/_80_include_engagement_context.py`

Injects into every prompt:
- Active engagement name + target
- Current scope summary
- Finding count by severity
- Last tool run + timestamp

### 4d. `agents/hacker/extensions/agent_init/_20_load_engagement.py`

On agent init: checks if an active engagement exists in memory, restores context automatically.

---

## Phase 5 — Skills and Knowledge Base

### 5a. Pentest Methodology Skill (`usr/skills/pentest_methodology.md`)

YAML frontmatter:
```yaml
name: pentest_methodology
description: Standard penetration testing phases and checklists
trigger_patterns:
  - "how do I start a pentest"
  - "pentest checklist"
  - "engagement phases"
```

Content: Full PTES/OWASP methodology checklist per phase.

### 5b. Tool Cheatsheets (`usr/skills/`)

One skill file per major tool category:
- `skill_nmap.md` — common scan types, NSE scripts, output formats
- `skill_metasploit.md` — module search patterns, payload selection, session management
- `skill_web_testing.md` — ffuf/gobuster wordlists, sqlmap flags, burp intruder patterns
- `skill_privesc.md` — Linux/Windows privilege escalation checklist, linpeas/winpeas interpretation
- `skill_ad_attacks.md` — BloodHound queries, Kerberoasting, Pass-the-Hash, DCSync

### 5c. Report Template (`usr/skills/pentest_report_template.md`)

Markdown template with CVSS scoring guide, finding severity definitions, executive summary boilerplate.

### 5d. CVE Knowledge Import (`usr/knowledge/`)

Import periodic snapshots of:
- CVSS scoring guide
- OWASP Top 10 (current year)
- Common service vulnerability patterns

Use `import_knowledge` API endpoint or run `knowledge_reindex` after dropping files.

---

## Phase 6 — Docker and Infrastructure

### 6a. `docker/Dockerfile.pentest` (new file)

Extends the base Agent Zero Kali image:

```dockerfile
FROM agent0ai/agent-zero:latest

# Ensure kali tooling is present
RUN apt-get update && apt-get install -y \
    amass gobuster ffuf nuclei \
    bloodhound neo4j \
    seclists \
    weasyprint \
    python3-impacket \
    && rm -rf /var/lib/apt/lists/*

# Pre-extract rockyou
RUN gunzip -k /usr/share/wordlists/rockyou.txt.gz 2>/dev/null || true

# Engagement workspace
RUN mkdir -p /a0/usr/workdir/engagements

# Install Python deps for new tools
RUN /opt/venv-a0/bin/pip install requests nvdlib shodan
```

### 6b. `docker/docker-compose.pentest.yml`

```yaml
version: '3.8'
services:
  agent-pentest:
    build:
      context: ..
      dockerfile: docker/Dockerfile.pentest
    ports:
      - "50001:80"
    environment:
      - A0_SET_agent_profile=hacker
      - A0_SET_shell_interface=local
    volumes:
      - ./usr/workdir/engagements:/a0/usr/workdir/engagements
      - ./usr/memory:/a0/usr/memory
    network_mode: bridge   # swap to host for actual network testing
    cap_add:
      - NET_ADMIN          # for wireless/packet tools
      - NET_RAW
```

### 6c. `agents/hacker/settings.json`

```json
{
  "agent_profile": "hacker",
  "agent_memory_subdir": "hacker",
  "workdir_path": "usr/workdir/engagements"
}
```

---

## Implementation Order

| Step | What | Effort |
|------|------|--------|
| 1 | Rewrite hacker role + environment prompts | Low — edit 2 files |
| 2 | Add solving.md + communication.md overrides | Low — create 2 files |
| 3 | Create recon, exploit-dev, reporter profiles | Medium — 3 × 2 files |
| 4 | Build `engagement_init.py` + `findings_tracker.py` tools | Medium — 2 Python files |
| 5 | Build `scope_check.py` + `scope_enforcement` extension | Medium — enforces safety |
| 6 | Build `report_generator.py` + `cve_lookup.py` tools | Medium — 2 Python files |
| 7 | Add 4 extensions (context injection, findings auto-save, etc.) | Medium — 4 Python files |
| 8 | Add tool prompts for new tools in hacker/prompts/ | Low — 4 markdown files |
| 9 | Write skills files (cheatsheets + methodology) | Low — markdown only |
| 10 | Dockerfile.pentest + docker-compose.pentest.yml | Low — 2 config files |

**Total new files: ~25–30. Zero changes to core framework code.**

---

## Key Design Decisions

**Scope enforcement is mandatory** — the `scope_enforcement` extension (4a) is the most important safety component. Without it, an autonomous agent with terminal access to Kali Linux will inevitably hit unintended targets. Every tool call that involves a network address must pass through scope validation.

**Engagement workspace isolation** — each target gets its own directory tree under `engagements/<target>/`. This prevents findings from one engagement contaminating another, and makes evidence collection and report generation deterministic.

**Sub-agents are specialized, not clones** — the `recon` agent has no exploitation tools in its prompt. The `exploit-dev` agent has no reporting tools. This reduces prompt pollution and makes each sub-agent's behavior predictable under delegation.

**Report generation is a first-class tool** — findings are structured data from the start (`findings.json`), not just chat output. This enables automated report generation and makes the engagement evidence defensible.
