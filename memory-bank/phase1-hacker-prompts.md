# Phase 1 — Hacker Agent Core Prompts

## Status: COMPLETE

## What Was Done

Rewrote and extended the `agents/hacker/prompts/` directory. The profile previously had only two stub files totalling ~16 lines. It now has four full prompt files covering the agent's identity, environment, methodology, and communication style.

---

## Files Changed / Created

### `agents/hacker/prompts/agent.system.main.role.md` (rewritten)

**Before:** 9-line stub — role name, employer type, "obey instructions", "cracking hacking part of job".

**After:** Full structured role specification including:
- Core identity as an autonomous Elite Penetration Tester
- Six professional capability categories: Network Penetration, Web Application, Exploit Dev, Post-Exploitation, CVE Research, Reporting
- Operational directives (scope enforcement, high-agency mindset, direct execution)
- Full 6-phase pentest methodology embedded in the prompt:
  - Phase 0: Scope & RoE initialization via `engagement_init` tool
  - Phase 1: Passive Reconnaissance (OSINT, DNS, Shodan)
  - Phase 2: Active Scanning (nmap, gobuster, service enum)
  - Phase 3: Vulnerability Analysis (CVE correlation, searchsploit)
  - Phase 4: Exploitation (Metasploit, manual PoC, evidence capture)
  - Phase 5: Post-Exploitation (privesc, credential harvest, lateral movement)
  - Phase 6: Reporting (findings_tracker → report_generator)

---

### `agents/hacker/prompts/agent.system.main.environment.md` (rewritten)

**Before:** 7-line stub — "kali linux docker", "utilize kali tools", "wordlists need downloading".

**After:** Full environment reference with:
- Tool inventory organized by category (Recon, Web, Exploit, Password, Post-Exploit, Wireless, Forensics) as markdown tables with tool names and purposes
- Wordlist paths with install fallback commands
- Engagement workspace directory structure explanation (`engagements/<target>/` layout)
- Network considerations: Docker bridge vs host mode, NET_ADMIN/NET_RAW capabilities, proxychains for pivoting
- Python exploit development notes (venv paths, available libraries)

---

### `agents/hacker/prompts/agent.system.main.solving.md` (new file)

Pentest-specific problem-solving prompt replacing the generic `prompts/agent.system.main.solving.md`. Covers:
- Initialize → Recall → Enumerate → Subtask → Execute → Track → Complete loop
- Fallback table: what to try when each tool fails
- High-agency mindset section emphasizing cross-finding correlation
- Delegation rules for specialist sub-agents

---

### `agents/hacker/prompts/agent.system.main.communication.md` (new file)

Defines the agent's output format for:
- Per-action format during an engagement (Action / Command / Result / Next)
- Per-vulnerability finding format with CVSS table, description, PoC steps, impact, remediation
- End-of-phase engagement summary format
- Subordinate delegation briefing format
- Escalation / blocker reporting protocol

---

## Why These Changes Matter

The hacker profile previously had no methodology — the LLM would produce reasonable results based on its training alone, but with no structured guidance it would skip phases, miss enumeration steps, and produce inconsistent output formats. These prompts give the agent an explicit execution framework so it consistently follows reconnaissance-before-exploitation order, tracks findings as structured data from the start, and produces findings reports that can be consumed by the `report_generator` tool.
