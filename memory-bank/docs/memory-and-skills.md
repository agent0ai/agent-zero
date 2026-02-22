# Memory & Skills

> **Navigation:** [Index](./index.md) | [Architecture](./architecture.md) | [Agent Profiles](./agent-profiles.md) | [Tools](./tools.md) | [Extensions](./extensions.md) | [Prompt System](./prompt-system.md) | [Configuration](./configuration.md)

---

## Memory System Overview

Agent Zero uses a **FAISS vector database** for persistent semantic memory. Agents can save information to memory and recall it by semantic similarity across sessions. Each agent profile has its own isolated memory subdirectory to prevent cross-contamination.

**Implementation:** `python/helpers/memory.py`

---

## Memory Architecture

```
Memory
├── FAISS index (cosine similarity)
│   └── backed by SentenceTransformer embeddings
├── Persistent on disk (usr/memory/<subdir>/)
└── Cached in-process (Memory.index dict)
```

**Backend:**
- **Vector DB:** FAISS (Facebook AI Similarity Search) via LangChain
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` via HuggingFace (default)
- **Distance metric:** Cosine similarity with L2 normalization
- **Cache:** Embedding cache stored in `tmp/memory/embeddings/` for performance

---

## Memory Areas

Every memory entry is tagged with an `area`. Three areas are defined:

| Area | Enum value | Purpose |
|------|-----------|---------|
| **Main** | `"main"` | General facts, user information, engagement data, anything that doesn't fit below |
| **Fragments** | `"fragments"` | Partial information, work-in-progress notes, intermediate results |
| **Solutions** | `"solutions"` | Verified successful solutions to technical problems — reused on similar future problems |

Filtering by area: pass `filter="area=='solutions'"` to `memory_load` or the `Memory.search_similarity_threshold()` method.

---

## Memory API

### Memory class (python/helpers/memory.py)

```python
# Get or initialize memory for an agent
memory = await Memory.get(agent)

# Get by explicit subdir (bypasses agent config)
memory = await Memory.get_by_subdir("hacker", log_item=None, preload_knowledge=True)

# Save text
memory_id = await memory.insert_text(text, metadata={"area": "main", "key": "value"})

# Semantic search
docs = await memory.search_similarity_threshold(
    query="SQL injection findings",
    limit=10,
    threshold=0.7,
    filter="area=='solutions'"
)

# Delete by IDs
deleted = await memory.delete_documents_by_ids(["id1", "id2"])

# Delete by semantic query
deleted = await memory.delete_documents_by_query(
    query="old engagement data",
    threshold=0.8,
    filter=""
)
```

### Document metadata schema

```python
{
    "id": "a3f9k2",           # Random 10-char ID (auto-generated)
    "timestamp": "2026-02-22 14:30:00",
    "area": "main",           # or "fragments" / "solutions"
    # + any custom kwargs from tool call
}
```

---

## Memory Tools

Four tools wrap the Memory API for the LLM to call directly. See [tools.md](./tools.md#memory-tools) for parameter details.

| Tool | Action |
|------|--------|
| `memory_save` | Save text + metadata |
| `memory_load` | Semantic search with threshold and filter |
| `memory_delete` | Delete by IDs |
| `memory_forget` | Delete by semantic query |

---

## Memory Storage

Files on disk per agent subdirectory:

```
usr/memory/<agent_memory_subdir>/
├── index.faiss          # FAISS vector index
├── docstore.pkl         # LangChain document store
├── index.pkl            # Index ↔ document mapping
├── embedding.json       # Embedding model metadata (for change detection)
└── knowledge_import.json  # Knowledge file sync tracking (hash-based)
```

**Profile isolation:** The `agent_memory_subdir` setting controls which directory the agent reads and writes. The hacker profile sets `"agent_memory_subdir": "hacker"` so its FAISS index is completely separate from other profiles. Changing the model or subdir triggers automatic re-indexing.

---

## Automatic Memory Operations

Two extensions run after every response to automatically build memory:

### `_50_memorize_fragments.py` (hook: monologue_end)

Extracts notable facts from the conversation using the utility LLM and saves them to memory (area=`fragments`). This captures useful tidbits without requiring the main agent to explicitly call `memory_save`.

### `_51_memorize_solutions.py` (hook: monologue_end)

Extracts problem/solution pairs from the conversation and saves them to memory (area=`solutions`). When a similar problem arises in the future, `_50_recall_memories.py` recalls these solutions and injects them into the system prompt.

### `_50_recall_memories.py` (hook: message_loop_prompts_after)

On every message loop iteration (or every N iterations, configurable), performs a semantic search of memory using the current context as the query. Injects top-k results into `extras_temporary` so they appear in the system prompt.

---

## Memory Recall Settings

Configured in `usr/settings.json`. See [configuration.md#memory-recall](./configuration.md#memory-recall) for all settings.

Key settings:

| Setting | Default | Effect |
|---------|---------|--------|
| `memory_recall_enabled` | `true` | Toggle automatic recall |
| `memory_recall_interval` | `3` | Recall every N iterations |
| `memory_recall_similarity_threshold` | `0.7` | Minimum cosine similarity to include |
| `memory_recall_memories_max_result` | `5` | Max general memories returned |
| `memory_recall_solutions_max_result` | `3` | Max solution memories returned |
| `memory_memorize_enabled` | `true` | Toggle automatic memorization |
| `memory_memorize_replace_threshold` | `0.9` | If similarity > 0.9, replace existing memory instead of adding duplicate |

---

## Knowledge Base

The knowledge base is a set of static files (text, PDF, markdown) that are pre-indexed into memory at startup. This allows the agent to answer questions about domain knowledge without needing web search.

**Directories:**

```
knowledge/           # Built-in framework knowledge
usr/knowledge/       # Custom user-added knowledge
usr/knowledge/<subdir>/  # Organized by topic
```

**Knowledge import tracking:** Each knowledge file is tracked by content hash in `knowledge_import.json`. On startup, the framework checks for added, modified, or removed files and syncs the FAISS index accordingly.

---

## Skills System

Skills are reusable knowledge modules stored as `SKILL.md` files. Unlike memory (which is automatically recalled), skills are **explicitly loaded on demand** when the agent determines they're relevant.

**Implementation:** `python/helpers/skills.py`

---

## SKILL.md Format

Every skill is a markdown file with a YAML frontmatter block at the top:

```yaml
---
name: skill-name           # Required: 1-64 chars, lowercase, hyphens only
description: >             # Required: ≤1024 chars — shown in skills list
  What this skill covers and when to use it.
version: "1.0"             # Optional
author: name               # Optional
tags: [tag1, tag2]         # Optional: for search
trigger_patterns:          # Optional: phrases that suggest loading this skill
  - "nmap scan"
  - "port scan"
  - "service detection"
allowed_tools: []          # Optional: restrict which tools this skill uses
license: MIT               # Optional
compatibility: ""          # Optional: ≤500 chars
metadata: {}               # Optional: arbitrary key/value
---

# Skill content starts here

Markdown content with commands, examples, checklists...
```

**Name validation:** lowercase letters, digits, and hyphens only; no leading/trailing hyphens; no double hyphens (`--`).

---

## Skill Discovery

Skills are discovered from multiple directories:

```
1. skills/                      # Built-in framework skills
2. usr/skills/                  # User-added custom skills
3. agents/*/skills/             # Profile-specific skills
4. usr/agents/*/skills/         # User overrides per profile
5. (active project skills)      # Per-project skills
```

Skills at earlier positions take precedence when multiple skills share the same name.

---

## Skill Loading

Skills have two states:

1. **Listed** — skill name and description appear in `agent.system.skills.md` in every system prompt. The agent sees what skills are available.
2. **Loaded** — skill content is injected into `agent.system.skills.loaded.md`. Only happens when the agent explicitly calls `skills_tool` with method=`load`.

Maximum 5 skills can be loaded simultaneously.

The agent uses `trigger_patterns` as hints for when to load a skill, but the final decision is the LLM's.

---

## Hacker Profile Skills

Six skills created for the hacker profile, stored in `usr/skills/`:

### pentest_methodology

**File:** `usr/skills/pentest_methodology.md`
**Triggers:** `pentest checklist`, `engagement phases`, `PTES`, `OWASP testing guide`, `penetration testing methodology`

7-phase penetration testing methodology with:
- Phase checklist with specific commands for each phase
- Decision tree (what to do when you find X)
- Engagement tracking checkboxes
- Scope verification steps
- Report writing guidance

---

### skill_nmap

**File:** `usr/skills/skill_nmap.md`
**Triggers:** `nmap`, `port scan`, `service scan`, `OS detection`, `NSE scripts`, `network scanning`

Nmap reference guide including:
- Scan type comparison table (SYN, TCP, UDP, SCTP, ACK, FIN, Xmas, null)
- Timing templates (`-T0` through `-T5`) with use cases
- Key flags (`-sV`, `-O`, `-A`, `-p-`, `-Pn`, `--open`)
- NSE script categories and common scripts
- Output format options (`-oN`, `-oX`, `-oG`, `-oA`)
- Evasion techniques (fragmentation, decoys, source port spoofing)
- Common workflows (quick scan → version scan → full port scan)

---

### skill_metasploit

**File:** `usr/skills/skill_metasploit.md`
**Triggers:** `metasploit`, `msfconsole`, `msfvenom`, `msf module`, `exploit module`, `metasploit session`, `meterpreter`

Metasploit Framework reference including:
- `msfconsole` commands (search, use, info, set, show options, run/exploit)
- Module types (exploits, auxiliary, post, payloads, encoders, NOPs)
- Meterpreter commands (sysinfo, getuid, upload/download, shell, getsystem)
- `msfvenom` payload generation for all platforms:
  - Linux ELF (x86/x64)
  - Windows EXE/DLL/PS1/HTA
  - Web payloads (WAR, JSP, PHP)
  - Android APK
  - Encoding for AV evasion (`-e x86/shikata_ga_nai`)
- Database setup (`db_nmap`, `hosts`, `services`, `vulns`)
- Handler setup (multi/handler, LHOST, LPORT)

---

### skill_web_testing

**File:** `usr/skills/skill_web_testing.md`
**Triggers:** `web application testing`, `web pentest`, `gobuster`, `ffuf`, `sqlmap`, `SQL injection`, `XSS`, `SSRF`, `OWASP`, `directory brute`

Web application testing reference including:
- Directory and file fuzzing (gobuster, ffuf with wordlists)
- SQL injection: manual detection, `sqlmap` usage, blind SQLi
- XSS: reflected, stored, DOM-based payloads
- SSRF: AWS metadata endpoint, internal port scan
- File upload bypasses (extension, MIME type, double extension)
- Authentication bypass techniques
- API testing (endpoint discovery, method fuzzing, auth bypass)
- Common vulnerability checkers (nikto, nuclei)
- OWASP Top 10 testing checklist

---

### skill_privesc

**File:** `usr/skills/skill_privesc.md`
**Triggers:** `privilege escalation`, `privesc`, `linpeas`, `winpeas`, `SUID`, `sudo exploit`, `escalate privileges`, `root`, `SYSTEM`, `kernel exploit`

Privilege escalation reference for both Linux and Windows:

**Linux:**
- linpeas.sh automated check
- SUID binaries (find command, GTFOBins reference)
- Sudo misconfigurations (`sudo -l`, NOPASSWD, wildcard abuse)
- Cron job abuse (writable scripts, PATH hijacking)
- Kernel exploits (uname -r, local exploit suggester)
- Weak file permissions (writable /etc/passwd, /etc/shadow)
- Capabilities (`getcap -r /`)
- Docker/LXC escape techniques

**Windows:**
- winpeas.exe automated check
- Token impersonation (Potato attacks: JuicyPotato, PrintSpoofer, RoguePotato)
- Weak service permissions
- Unquoted service paths
- AlwaysInstallElevated
- Credential hunting (registry, files, SAM dump)
- mimikatz (sekurlsa, lsadump)

---

### skill_ad_attacks

**File:** `usr/skills/skill_ad_attacks.md`
**Triggers:** `active directory`, `AD attack`, `kerberoasting`, `AS-REP roasting`, `pass the hash`, `BloodHound`, `DCSync`, `NTLM relay`, `domain controller`, `ldap enumeration`

Active Directory attack reference including:
- Enumeration (ldapdomaindump, enum4linux-ng, bloodhound-python)
- BloodHound (data collection, Cypher queries for attack paths)
- Kerberoasting: `GetUserSPNs.py`, hashcat cracking
- AS-REP Roasting: `GetNPUsers.py`, hashcat mode 18200
- Pass-the-Hash (PtH): impacket psexec/wmiexec/smbexec
- Pass-the-Ticket (PtT): extracting and using TGTs/TGSs
- NTLM relay (Responder + ntlmrelayx)
- DCSync: secretsdump.py from domain-joined context
- Golden ticket: domain SID + krbtgt hash → persistent access
- Silver ticket: service hash → forged TGS
- Lateral movement (crackmapexec, evil-winrm)

---

## Memory vs Skills Summary

| Feature | Memory | Skills |
|---------|--------|--------|
| Storage | FAISS vector DB | Markdown files (`SKILL.md`) |
| When populated | Automatically (by extensions) or manually (by agent) | Created manually by users/developers |
| When recalled | Automatic (every N iterations) or on demand | On demand via `skills_tool` |
| Content | Dynamic — learned from conversations | Static — pre-written reference material |
| Searchable | Vector similarity (semantic) | Fuzzy text + vector similarity |
| Per-profile isolation | Via `agent_memory_subdir` | Via skill root directories |
| Limit | Thousands of entries | Max 5 loaded simultaneously |
| Purpose | Episodic memory, learned facts | Reference guides, checklists, how-tos |
