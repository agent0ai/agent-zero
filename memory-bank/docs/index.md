# agent-zero-sec — Documentation Index

> **Agent Zero Security Variant** — an autonomous penetration testing framework built on the Agent Zero multi-agent architecture, running on a Kali Linux Docker container with full toolchain integration.

---

## Documentation Map

| File | What it covers |
|------|---------------|
| **[architecture.md](./architecture.md)** | Agent message loop, extension hooks, tool dispatch, prompt assembly, LLM integration, multi-agent communication |
| **[agent-profiles.md](./agent-profiles.md)** | All 9 agent profiles, the profile override system, how to create a custom profile |
| **[tools.md](./tools.md)** | All 24 active tools — base class, standard tools, and the 5 new pentest tools |
| **[extensions.md](./extensions.md)** | All 25 extension hooks, 39+ extensions, profile-specific overrides, how to write extensions |
| **[prompt-system.md](./prompt-system.md)** | 102 prompt template files, include directives, variable injection, profile overrides |
| **[memory-and-skills.md](./memory-and-skills.md)** | FAISS vector memory, memory areas, skills system, all hacker profile skills |
| **[configuration.md](./configuration.md)** | Settings hierarchy, all settings with defaults, Docker setup, environment variables, API keys |
| **[pentest-workflow.md](./pentest-workflow.md)** | End-to-end penetration test guide using the hacker profile |

**Implementation logs** (how this project was built):

| File | Content |
|------|---------|
| [IMPLEMENTATION.md](./IMPLEMENTATION.md) | Complete implementation record with all design decisions |
| [phase1-hacker-prompts.md](./phase1-hacker-prompts.md) | Hacker prompt rewrite details |
| [phase2-sub-agent-profiles.md](./phase2-sub-agent-profiles.md) | Sub-agent profile creation |
| [phase3-pentest-tools.md](./phase3-pentest-tools.md) | Python tool implementation |
| [phase4-extensions.md](./phase4-extensions.md) | Extension implementation |
| [phase5-skills-settings.md](./phase5-skills-settings.md) | Skills and settings |
| [phase6-docker.md](./phase6-docker.md) | Docker infrastructure |

---

## Quick Start

```bash
# Build and launch the pentest agent
docker compose -f docker/pentest/docker-compose.yml up --build

# Access the web UI
open http://localhost:50001

# First prompt to start an engagement
# "Initialize an engagement for target 10.10.10.5 with scope 10.10.10.0/24"
```

See [pentest-workflow.md](./pentest-workflow.md) for the full engagement guide.

---

## What is Agent Zero

Agent Zero is a hierarchical multi-agent AI framework. Agents receive instructions, think using an LLM, call tools, and spawn subordinate agents to delegate subtasks. Every behavior is controlled by markdown prompt files — no hard-coded logic.

**agent-zero-sec** is a security-focused fork with:
- A `hacker` agent profile with full pentest methodology
- 5 new tools: engagement workspace, findings tracking, scope enforcement, report generation, CVE lookup
- 4 profile-specific extensions: scope enforcement, session restore, context injection, auto-save reminders
- 3 specialist sub-agent profiles: `recon`, `exploit-dev`, `reporter`
- 6 skill files covering nmap, Metasploit, web testing, privilege escalation, AD attacks, and methodology

---

## Project Structure

```
agent-zero-sec/
│
├── agent.py                    # Core: AgentContext, Agent class, AgentConfig
├── models.py                   # LLM abstraction via LiteLLM
├── initialize.py               # AgentConfig builder from settings
├── run_ui.py                   # Flask + Uvicorn + SocketIO web server
│
├── agents/                     # Agent profiles (9 total)
│   ├── agent0/                 # Default user-facing agent
│   ├── hacker/                 # ★ Penetration testing agent (primary profile)
│   │   ├── settings.json       # Profile settings override
│   │   ├── prompts/            # 9 prompt overrides + 5 tool prompt docs
│   │   └── extensions/         # 4 profile-specific extensions
│   ├── recon/                  # ★ Reconnaissance specialist (new)
│   ├── exploit-dev/            # ★ Exploit development specialist (new)
│   ├── reporter/               # ★ Report generation specialist (new)
│   ├── developer/              # Software development specialist
│   ├── researcher/             # Research and analysis specialist
│   ├── default/                # Fallback profile
│   └── _example/               # Template for custom profiles
│
├── prompts/                    # 102 global prompt template files
│   ├── agent.system.main.md    # Root system prompt (composes all others)
│   ├── agent.system.tool.*.md  # Tool documentation prompts
│   ├── fw.*.md                 # Framework feedback messages
│   └── memory.*.md             # Memory system prompts
│
├── python/
│   ├── tools/                  # 29 tool files (5 new pentest tools)
│   │   ├── code_execution_tool.py
│   │   ├── call_subordinate.py
│   │   ├── engagement_init.py  # ★ new
│   │   ├── findings_tracker.py # ★ new
│   │   ├── scope_check.py      # ★ new
│   │   ├── report_generator.py # ★ new
│   │   └── cve_lookup.py       # ★ new
│   ├── extensions/             # 39 framework extensions across 25 hooks
│   ├── api/                    # 74 REST API endpoints
│   ├── websocket_handlers/     # WebSocket handlers
│   └── helpers/                # 86+ utility modules
│
├── usr/
│   ├── settings.json           # User settings (written by UI)
│   ├── workdir/                # Agent working directory
│   │   └── engagements/        # ★ Pentest engagement workspaces
│   ├── memory/                 # FAISS vector index per memory_subdir
│   ├── skills/                 # ★ 6 hacker skill files (new)
│   └── knowledge/              # Knowledge base files for RAG
│
├── skills/                     # Built-in system skills
├── conf/
│   └── model_providers.yaml    # 21 chat + 9 embedding provider configs
│
├── docker/
│   ├── run/                    # Standard docker-compose.yml + Dockerfile
│   └── pentest/                # ★ Pentest-focused Docker image (new)
│       ├── Dockerfile
│       └── docker-compose.yml
│
└── memory-bank/                # Project documentation
    └── docs/                   # ← you are here
```

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| LLM orchestration | [LiteLLM](https://github.com/BerriAI/litellm) — 25+ provider abstraction |
| Default chat model | `anthropic/claude-sonnet-4.6` via OpenRouter |
| Default util model | `google/gemini-3-flash-preview` via OpenRouter |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` via HuggingFace |
| Vector database | FAISS with SentenceTransformer embeddings |
| Web server | Flask + Uvicorn + SocketIO |
| Process management | Supervisord |
| Container OS | Kali Linux |
| Browser automation | Playwright |
| Code execution | IPython (Python), Node.js, Bash |
| Web search | SearXNG (self-hosted) |
