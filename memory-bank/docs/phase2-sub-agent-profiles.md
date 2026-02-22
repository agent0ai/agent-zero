# Phase 2 — Sub-Agent Profiles

## Status: COMPLETE

## What Was Done

Created three new specialist agent profiles that the hacker (superior) agent can delegate to via the `call_subordinate` tool. Each profile has a focused scope that prevents capability overlap and reduces prompt pollution.

---

## Files Created

### `agents/recon/`

**Purpose:** Reconnaissance-only agent. No exploitation.

| File | Description |
|------|-------------|
| `agent.json` | Title: "Recon Specialist". Description emphasizes discovery-only, no exploitation. |
| `prompts/agent.system.main.role.md` | Full passive + active recon methodology with precise output formats for port scan summaries, web fingerprints, and OSINT summaries. Lists tools by category with key flags. |
| `prompts/agent.system.main.environment.md` | Tool reference table (nmap, masscan, amass, theHarvester, subfinder, gobuster, ffuf, whatweb, wafw00f, sslscan, dnsrecon, enum4linux-ng, snmpwalk) with wordlist paths. |

**Key design decision:** The role explicitly states "you do NOT exploit" and "non-destructive only: no exploitation, no password attempts, no payload delivery". This means even if the LLM detects a vulnerability during scanning, it will not attempt to use it — it reports it to the superior agent.

---

### `agents/exploit-dev/`

**Purpose:** Exploit research, adaptation, and payload generation.

| File | Description |
|------|-------------|
| `agent.json` | Title: "Exploit Developer". Description specifies CVE/service input → working payload output. |
| `prompts/agent.system.main.role.md` | Covers exploit research (searchsploit, GitHub, Metasploit), msfvenom payload generation, exploit adaptation (offset adjustment, Python 2/3 fixes, AV evasion), and custom exploit development (buffer overflow, web exploits, impacket scripts). Includes a standardized exploit delivery output format. |
| `prompts/agent.system.main.communication.md` | Output standards: complete working code only, no scaffolds. Failure protocol: what to report when adaptation fails. Security annotations: stability risk, noise level, cleanup notes. |

**Key design decision:** The exploit delivery output format is structured to match what the `findings_tracker` tool expects — it includes host, port, CVE, and evidence path fields. This makes it easy for the superior hacker agent to pipe exploit-dev output directly into a finding entry.

---

### `agents/reporter/`

**Purpose:** Convert `findings.json` into professional pentest report deliverables.

| File | Description |
|------|-------------|
| `agent.json` | Title: "Security Reporter". Description specifies findings.json input → report output. |
| `prompts/agent.system.main.role.md` | Full report structure: Cover Page, Executive Summary, Scope & Methodology, Risk Rating Matrix, Findings (CVSS-sorted), Appendix. CVSS 3.1 scoring guidance for new findings. Three output formats: Markdown, HTML (CSS-styled), PDF (via weasyprint). |
| `prompts/agent.system.main.communication.md` | Tone guidance (executive vs technical), formatting rules, evidence reference standards, completeness checklist. |

**Key design decision:** The reporter role explicitly says "never fabricate findings — only report what is in findings.json". This prevents the LLM from inventing plausible-sounding vulnerabilities to fill out a report.

---

## How the Hierarchy Works

```
User
  └── hacker (superior, orchestrates)
        ├── recon    (Phase 1-2: enumeration only)
        ├── exploit-dev  (Phase 4: payload delivery)
        └── reporter     (Phase 6: final report)
```

The hacker agent can spawn any of these as needed via:
```json
{
  "tool_name": "call_subordinate",
  "tool_args": {
    "message": "Enumerate all services on 10.10.10.5 and return a structured port scan summary",
    "agent_profile": "recon"
  }
}
```
