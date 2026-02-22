# Phase 5 — Skills, Knowledge Base, and Hacker Settings

## Status: COMPLETE

## What Was Done

Created 5 skill files in `usr/skills/`, one hacker profile `settings.json`.

---

## Files Created

### `usr/skills/pentest_methodology.md`

Full penetration testing methodology reference with:
- Phase 0: Engagement setup checklist (authorization, scope, RoE, workspace init)
- Phase 1: Passive recon OSINT checklist with tool commands (amass, theHarvester, subfinder, crt.sh, Shodan)
- Phase 2: Active scanning workflows (nmap, masscan, gobuster, ffuf, service-specific enum for SMB/SNMP/NFS/SSH/FTP/LDAP)
- Phase 3: Vulnerability analysis (cve_lookup, searchsploit, nuclei, prioritization matrix)
- Phase 4: Exploitation checklist with proof capture commands for Linux and Windows
- Phase 5: Post-exploitation (linpeas, winpeas, credential harvest, lateral movement)
- Phase 6: Reporting checklist (findings_tracker → report_generator)
- Decision tree: "I found a port — what next?" for HTTP, SMB, SSH, databases, unknown services

**Trigger patterns:** "pentest checklist", "how do I start a pentest", "engagement phases", "PTES"

---

### `usr/skills/skill_nmap.md`

Nmap reference covering:
- All major scan types (`-sS`, `-sT`, `-sU`, `-sV`, `-sC`, `-O`, `-sN/F/X`, `-sA`) with use cases
- Port selection flags and timing templates table
- 3-phase workflow: discovery → full port scan (masscan first) → vuln scan
- NSE script categories with use cases
- Per-service NSE script examples (SMB, HTTP, FTP, SSH, SMTP)
- Output formats (`-oN`, `-oX`, `-oG`, `-oA`)
- Evasion techniques (decoys, fragmentation, custom source port, random host order, MAC spoof)
- How to read nmap output (open/filtered/closed meanings)

---

### `usr/skills/skill_metasploit.md`

Metasploit Framework reference covering:
- Starting Metasploit (database init, msfconsole, resource scripts, one-liner mode)
- Module search and selection syntax
- Module configuration commands
- Payload selection guide (staged vs stageless, Windows/Linux/web)
- msfvenom payload generation for all platforms: ELF, EXE, DLL, PS1, HTA, WAR, JSP, PHP, Python, Android APK
- Encoding and template injection for AV evasion
- Handler setup with `multi/handler`
- Complete Meterpreter command reference (sysinfo, getsystem, migrate, download/upload, portfwd, route)
- Post-exploitation modules (local_exploit_suggester, hashdump, credential_collector, persistence)
- Database integration (workspaces, db_nmap, hosts/services/vulns/loot/creds commands)
- Resource script creation

---

### `usr/skills/skill_web_testing.md`

Web application penetration testing reference covering:
- Directory and file discovery (gobuster, ffuf, feroxbuster) with wordlist paths
- Virtual host / subdomain discovery with ffuf Host header fuzzing
- SQL injection: manual payloads, sqlmap with GET/POST/cookie, blind, OS shell
- XSS: basic payloads, DOM sinks, dalfox
- SSRF: basic payloads, internal service discovery, protocol confusion, bypass techniques
- File upload bypass: content-type, double extension, case variation, alternative PHP extensions
- Authentication testing: default credentials, Hydra brute force examples
- Command injection payloads
- API testing: endpoint discovery, IDOR, mass assignment, GraphQL introspection
- Security header manipulation for path traversal and IP bypass
- Scanning tools: nikto, nuclei, wpscan

---

### `usr/skills/skill_privesc.md`

Privilege escalation reference for both platforms:

**Linux:** linpeas, SUID/SGID with GTFOBins examples, sudo misconfig with specific binary exploits, cron job injection (wildcard and script write), writable /etc/passwd, PATH injection, systemd service write, kernel CVEs (DirtyCow, DirtyPipe), capabilities (cap_setuid), Docker group escape.

**Windows:** winPEAS, SeImpersonatePrivilege + Potato exploits (GodPotato, PrintSpoofer, JuicyPotato), unquoted service paths, weak service permissions with accesschk, AlwaysInstallElevated MSI, credential hunting (config files, registry, Credential Manager, SAM/SYSTEM dump), mimikatz, token impersonation via incognito.

Ends with: post-privesc checklist.

---

### `usr/skills/skill_ad_attacks.md`

Active Directory attack reference covering:
- Unauthenticated enumeration (LDAP null bind, NetBIOS, DNS SRV records, MSRPC)
- Authenticated enumeration (crackmapexec, ldapdomaindump, PowerView, BloodHound Python collector)
- BloodHound Cypher queries (DA paths, session enumeration, Kerberoastable accounts, unconstrained delegation, AS-REP roastable)
- Kerberoasting (impacket-GetUserSPNs + hashcat -m 13100, Rubeus)
- AS-REP Roasting (impacket-GetNPUsers + hashcat -m 18200)
- Pass-the-Hash (crackmapexec, psexec, wmiexec, smbexec, evil-winrm)
- Pass-the-Ticket (mimikatz → impacket-ticketConverter → psexec -k)
- NTLM Relay (Responder + ntlmrelayx, relay-to-LDAP for RBCD)
- DCSync (impacket-secretsdump, mimikatz lsadump::dcsync)
- Golden Ticket (mimikatz + impacket-ticketer)
- Silver Ticket (impacket-ticketer with service hash)
- Lateral movement summary table
- Impacket tools quick reference table

---

### `agents/hacker/settings.json`

Profile-level settings override:
```json
{
  "agent_profile": "hacker",
  "agent_memory_subdir": "hacker",
  "workdir_path": "usr/workdir",
  "memory_recall_enabled": true,
  "memory_memorize_enabled": true
}
```

Sets the hacker profile as default, separates its memory from other profiles (`hacker` subdirectory instead of `default`), and explicitly enables memory to ensure findings and engagement context persist.

---

## How Skills Work

Skills use the SKILL.md standard with YAML frontmatter. The Agent Zero skills system vector-indexes the content and loads relevant skills contextually when the `trigger_patterns` match the user's query. This means the agent does not always have all cheatsheets in its context window — they are loaded on demand, keeping the system prompt clean.
