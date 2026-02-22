# Implementation Docs — Penetration Testing Agent

This directory documents every implementation step for the sec-agent build.

## Documents

| File | Phase | Status |
|------|-------|--------|
| [phase1-hacker-prompts.md](phase1-hacker-prompts.md) | Core hacker agent prompts | COMPLETE |
| [phase2-sub-agent-profiles.md](phase2-sub-agent-profiles.md) | Recon, exploit-dev, reporter profiles | COMPLETE |
| [phase3-pentest-tools.md](phase3-pentest-tools.md) | Python tools + tool prompts | COMPLETE |
| [phase4-extensions.md](phase4-extensions.md) | Scope enforcement + context extensions | COMPLETE |
| [phase5-skills-settings.md](phase5-skills-settings.md) | Skills, knowledge base, hacker settings | COMPLETE |
| [phase6-docker.md](phase6-docker.md) | Docker pentest image + compose file | COMPLETE |

## Files Created (full list)

### Agent Profiles
```
agents/hacker/prompts/agent.system.main.role.md         (rewritten)
agents/hacker/prompts/agent.system.main.environment.md  (rewritten)
agents/hacker/prompts/agent.system.main.solving.md      (new)
agents/hacker/prompts/agent.system.main.communication.md (new)
agents/hacker/prompts/agent.system.tool.engagement_init.md (new)
agents/hacker/prompts/agent.system.tool.findings_tracker.md (new)
agents/hacker/prompts/agent.system.tool.scope_check.md  (new)
agents/hacker/prompts/agent.system.tool.report_generator.md (new)
agents/hacker/prompts/agent.system.tool.cve_lookup.md   (new)
agents/hacker/settings.json                             (new)

agents/recon/agent.json                                 (new)
agents/recon/prompts/agent.system.main.role.md          (new)
agents/recon/prompts/agent.system.main.environment.md   (new)

agents/exploit-dev/agent.json                           (new)
agents/exploit-dev/prompts/agent.system.main.role.md    (new)
agents/exploit-dev/prompts/agent.system.main.communication.md (new)

agents/reporter/agent.json                              (new)
agents/reporter/prompts/agent.system.main.role.md       (new)
agents/reporter/prompts/agent.system.main.communication.md (new)
```

### Python Tools
```
python/tools/engagement_init.py   — workspace init, engagement lifecycle
python/tools/findings_tracker.py  — CRUD for vulnerability findings
python/tools/scope_check.py       — IP/domain/URL scope validation
python/tools/report_generator.py  — Markdown/HTML/PDF report generation
python/tools/cve_lookup.py        — NVD API + ExploitDB CVE research
```

### Extensions (hacker profile only)
```
agents/hacker/extensions/tool_execute_before/_05_scope_enforcement.py
agents/hacker/extensions/agent_init/_20_load_engagement.py
agents/hacker/extensions/message_loop_prompts_after/_80_include_engagement_context.py
agents/hacker/extensions/monologue_end/_55_auto_save_findings.py
```

### Skills
```
usr/skills/pentest_methodology.md
usr/skills/skill_nmap.md
usr/skills/skill_metasploit.md
usr/skills/skill_web_testing.md
usr/skills/skill_privesc.md
usr/skills/skill_ad_attacks.md
```

### Docker
```
docker/pentest/Dockerfile
docker/pentest/docker-compose.yml
```

## Quick Start

```bash
# Build and run the pentest agent
docker compose -f docker/pentest/docker-compose.yml up --build

# Open the UI
open http://localhost:50001

# In the UI: go to Settings → Agent Profile → select "hacker"
# Start with: "Initialize a new engagement for target 10.10.10.5 with scope 10.10.10.0/24"
```
