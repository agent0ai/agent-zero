# Autonomous Innovation Super-Agency Blueprint

This document describes how to configure the Agent Zero framework to run a fully autonomous research, development, and technology commercialization agency that rivals the combined capabilities of top-tier labs. It defines agent archetypes, department structures, and low-touch protocols designed to minimize human intervention while maintaining safety and governance.

---

## 1. Guiding Principles
- **Mission clarity first:** Every autonomous workflow begins with explicit OKRs and guardrails encoded in prompts and behavior rules.
- **Delegation by design:** Agents are expected to break problems into sub-missions and spin up specialized subordinates whenever scope grows.
- **Evidence over opinion:** All major decisions require citations via the knowledge tool, instrumentation logs, or code artifacts.
- **Continuous memory:** Insights graduate from transient context → working memory → persistent `memory/` or `knowledge/` as they prove reusable.
- **Governed autonomy:** Safety, compliance, and resource controls are enforced by dedicated watchdog agents that can halt pipelines.

---

## 2. Agent Tiers & Worker Archetypes

| Tier | Description | Primary Agents |
| --- | --- | --- |
| **Executive Cortex** | Owns agency-wide OKRs, budgets, and risk posture. Interfaces with the human sponsor. | Apex Orchestrator (Agent 0), Portfolio Navigator, Risk & Ethics Governor |
| **Domain Studios** | Department-level strategists that translate OKRs into thematic programs. | Research Studio Director, Product Systems Director, Platform Engineering Director, Venture & GTM Director |
| **Execution Pods** | Cross-functional squads that run experiments, build prototypes, and ship releases. | Research Fellows, ML Architects, Systems Engineers, Product Synthesists, Validation Analysts |
| **Support Mesh** | Shared services covering finance, vendor ops, compliance, talent, and facilities (virtual). | Autonomy Comptroller, Procurement Pilot, Talent Steward |
| **Autonomous Infrastructure** | Toolsmiths and observability agents that maintain instruments, logs, and knowledge graphs. | Instrument Engineer, Memory Librarian, Telemetry Sentinel |

Each archetype maps to a reusable prompt persona stored under `prompts/super-agency/agent.system.role.<persona>.md` and referenced from the main system prompt.

---

## 3. Department Blueprint & Agent Definitions

### 3.1 Strategic Command (Executive Cortex)
- **Apex Orchestrator:** Runs the top-level control loop, prioritizes missions, and approves resource allocations. Lives inside `agent.system.main.role.md`.
- **Portfolio Navigator:** Scores opportunities, manages the multi-horizon roadmap, and triggers new domain studios when capacity >70%.
- **Risk & Ethics Governor:** Monitors for policy violations using extension hooks `_30_guardrails.py`, can pause or roll back runs.

### 3.2 Research Intelligence & Emerging Science
- **Scouting Agents:** Continuously watch frontier literature using `knowledge_tool` + SearXNG, tag findings into `knowledge/custom/main`.
- **Program Architects:** Convert scouting signals into funded research programs with explicit success metrics.
- **Experiment Fabricators:** Use `python/tools/code_execution_tool` and instruments under `instruments/research_*` to run simulations, notebooks, or lab automations.

### 3.3 Product Systems & Experience Lab
- **Product Synthesists:** Translate research outputs into user-facing narratives, JTBD documents, and requirement specs saved in `docs/roadmaps/`.
- **Experience Choreographers:** Prototype UI flows leveraging `webui/` components or low-code instruments.
- **Adoption Analysts:** Instrument telemetry dashboards to test desirability and engagement hypotheses.

### 3.4 Engineering & Platform
- **Core Systems Engineers:** Extend `python/` services, own CI/CD, and steward technical debt registries.
- **ML/AI Engineers:** Package models, manage fine-tuning jobs, and maintain evaluation harnesses in `python/extensions/evals/`.
- **Automation Operators:** Build instruments (shell/python scripts) to interact with external infra, data lakes, or deployment targets.

### 3.5 Growth, Ventures & Partnerships
- **Ecosystem Cartographers:** Map ecosystems, scout potential partners, and maintain opportunity graphs in knowledge base.
- **Venture Analysts:** Run market sizing templates, diligence potential spin-outs, and simulate business scenarios.
- **Alliance Negotiators:** Generate outreach briefs, contract drafts, and negotiation trees.

### 3.6 Operations, Finance & Compliance
- **Autonomy Comptroller:** Monitors compute/token spend, enforces budgets using telemetry instruments.
- **Compliance Guardian:** Ensures every workflow references the latest policy packs stored under `docs/policies/`.
- **Talent Steward:** Manages agent prompt updates, onboarding checklists, and escalation routing.

---

## 4. Core Systems Mapped to the Repo

| Capability | Repo Anchor | Notes |
| --- | --- | --- |
| Prompt hierarchy | `prompts/default/` → `prompts/super-agency/` | Copy defaults, add persona-specific files, reference via settings. |
| Behavior rules | `behaviour/*.md` + `python/tools/behaviour_adjustment.py` | Executive Cortex updates rules at runtime for global pivots. |
| Tools & instruments | `python/tools/`, `instruments/` | Department-specific instruments encapsulate workflows without bloating prompts. |
| Memory & knowledge | `memory/`, `knowledge/`, `docs/` | Research insights and SOPs persist for reuse and grounding. |
| Extensions | `python/extensions/` | Add watchdog, telemetry, and summarization hooks to enforce autonomy constraints. |
| Web UI + CLI | `webui/`, `run_cli.py`, Docker stack | Enables monitoring dashboards and manual overrides if needed. |

---

## 5. Low-Touch Protocols & Workflows

### 5.1 Mission Intake & Prioritization
1. Human sponsor (or previous quarter review) drops intents into `docs/strategy/incoming.md`.
2. Apex Orchestrator ingests intents, runs scoring instrument (`instruments/strategy/score.sh`), and updates `behaviour.md` with fresh OKRs.
3. Portfolio Navigator spawns/updates Domain Studio agents with scoped mandates, dependencies, and resource envelopes.

### 5.2 Research Sprint Loop
1. Scouting Agents continuously run watchlists (scheduled via cron + CLI) and push summaries to knowledge base.
2. Program Architects cluster findings, design hypotheses, and enqueue experiments in `docs/research_backlog.md`.
3. Experiment Fabricators pull tasks, execute code/instruments, and auto-upload artifacts to `logs/` + `memory/solutions`.
4. Risk Governor samples results, checking for compliance or reproducibility flags before promotion.

### 5.3 Concept-to-Product Pipeline
1. Product Synthesist consumes validated research outputs and drafts Product Requirement Packs (PRPs).
2. Experience Choreographers auto-generate UX prototypes or narrative demos via `webui` tooling.
3. Core Systems Engineers size effort, generate milestones, and spawn Execution Pods per component.
4. Adoption Analysts configure telemetry instruments and success metrics before code freeze.

### 5.4 Build, Test, and Deployment Workflow
1. Execution Pods operate under Agile-by-default prompts: plan → implement → test via built-in code execution and unit suites.
2. Telemetry Sentinel extensions capture runtime logs, feeding Observability dashboards accessible via the Web UI.
3. Deployment scripts (Docker, CI/CD) run through automation operators; only Compliance Guardian or Apex Orchestrator can halt or approve final releases.

### 5.5 Knowledge Capture & Memory Hygiene
1. Every completed task triggers a `memory_tool` write: summary, decision, key artifacts.
2. Librarian agents promote recurring assets into `knowledge/custom/main` with embeddings.
3. Weekly automated maintenance jobs deduplicate, compress, or archive memories using `memory_tool forget` flows.

### 5.6 Governance & Minimal Human Interaction
- **Watchdog Extensions:** `_40_watchdog.py` evaluates tool outputs, halting loops on anomaly scores.
- **Budget Fuses:** Autonomy Comptroller reads telemetry instruments and updates behavior rules if spend > thresholds.
- **Compliance Hooks:** Policies stored in `docs/policies/` are injected into prompts for any workflow touching regulated domains.
- **Escalation Matrix:** Only Apex Orchestrator pings the human sponsor, and only when blockers exceed pre-defined severity.

---

## 6. Implementation Roadmap Inside Agent Zero

1. **Create Prompt Set:** Duplicate `prompts/default` → `prompts/super-agency`, customize role files per persona, update `agent.system.main.md` to reference the new set.
2. **Encode Departments:** For each department, define:
   - Role description snippet
   - Delegation heuristics (when to spawn sub-agents/instruments)
   - Required tools/instruments list
3. **Build Instruments:** Scaffold scripts under `instruments/<dept>/` for scoring, experiment automation, budgeting, telemetry, and knowledge ops.
4. **Register Extensions:** Add guardrail, telemetry, and planner extensions (numbered for execution order) under `python/extensions/`.
5. **Seed Knowledge:** Populate `knowledge/custom/main` with policy docs, partner intel, research taxonomies, and SOPs.
6. **Configure Schedules:** Use OS-level schedulers or Orchestrator cron to kick off recurring scouting, evaluation, and reporting loops.
7. **Observability Dashboard:** Expose telemetry via Web UI panels or external dashboards that consume `logs/` outputs.

---

## 7. Minimal Human Touchpoints
- **Quarterly OKR Refresh:** Sponsor reviews the Apex Orchestrator’s plan and adjusts funding envelopes.
- **Exception Handling:** Humans intervene only when watchdog agents escalate (safety, regulatory, catastrophic failure).
- **Validation Spot-Checks:** Optional human audits sample 5–10% of major releases for assurance.

By codifying the above structure inside Agent Zero’s prompt, memory, and instrument layers, the organization operates as a cohesive, autonomous innovation powerhouse with humans positioned purely as goal setters and safety reviewers.

---

## 8. Prompt Persona Template Library

### 8.1 Repository Layout
```
prompts/
  super-agency/
    agent.system.main.md
    agent.system.main.role.md
    agent.system.role.apex_orchestrator.md
    agent.system.role.portfolio_navigator.md
    agent.system.role.risk_governor.md
    agent.system.role.research_fellow.md
    ...
```
- Duplicate `prompts/default/*` into `prompts/super-agency/*` as a baseline.
- Update `settings.yml` (or Web UI Agent Config) to point at the new subdirectory.

### 8.2 Persona Snippet Template
Store each persona file as a reusable fragment referenced from `agent.system.main.role.md`.

```
### Persona: Apex Orchestrator
- Mission: translate sponsor intent into prioritized, budgeted missions for the entire agency.
- Delegation Rules: spawn Domain Studio Director when task spans >1 discipline; delegate to Support Mesh when budget/compliance implications arise.
- Mandatory Tools: knowledge_tool (for market context), behavior_adjustment (for OKR updates), call_subordinate.
- Required Outputs: OKR table, dependency map, escalation log.
- Guardrails: never commit resources without citing telemetry or research artifacts; always log plan revisions to memory.
```

### 8.3 Prompt Injection Hooks
- `agent.system.main.md`: reference each persona file using `{{file:prompts/super-agency/agent.system.role.<persona>.md}}`.
- `agent.system.tools.md`: include only tools relevant to the persona set to minimize token load.
- `behaviour.merge.msg.md`: keep persona-specific behavior overrides short; complex procedures should live in instruments.

---

## 9. Cross-Domain Workflow Protocols

### 9.1 Mission Orchestration Handshake
1. Apex Orchestrator receives new intent and runs the Scoring Instrument.
2. Portfolio Navigator compares active capacity vs. forecast and either:
   - Reprioritizes current missions, or
   - Spins up a new Domain Studio agent with a scoped charter.
3. Risk & Ethics Governor is pinged asynchronously with the proposed plan to attach mandatory compliance packets before work begins.

### 9.2 Research-to-Build Relay
1. Research Studio Director finalizes experiment bundle and pushes it to `docs/research_exports/<mission>/`.
2. Product Synthesist consumes bundle, drafts PRP, and logs it to memory with tag `prp:<mission>`.
3. Platform Engineering Director auto-generates work packages, ensuring each includes:
   - Linked artifacts (code, datasets)
   - Tool requirements
   - Acceptance tests and telemetry hooks
4. Execution Pod Agents pull work packages FIFO and report progress via subordinate agents or memory updates.

### 9.3 Feedback & Continuous Learning Loop
1. Telemetry Sentinel aggregates KPIs per mission and saves dashboards into `logs/dashboards/<mission>.html`.
2. Adoption Analysts and Venture Analysts subscribe to the same telemetry feed to derive user/market insights.
3. Portfolio Navigator evaluates KPI deltas weekly; if metrics fall below thresholds, it automatically issues a `behaviour_adjustment` request that tightens resource use or revises OKRs.
4. Librarian Agents promote new learnings into the knowledge base, tagging them with mission IDs and taxonomy labels for rapid retrieval.

### 9.4 Safety Net Protocol
- Guardrail extensions monitor:
  - Tool output sentiment / toxicity
  - Resource spikes
  - Compliance keyword hits
- On anomaly detection, `call_superior` is triggered with a structured report, pausing subordinate agents until Apex Orchestrator clears the incident or escalates to a human sponsor.

---

## 10. Instrument & Extension Scaffold Checklist

| Component | Location | Purpose |
| --- | --- | --- |
| `score.sh` | `instruments/strategy/` | Multi-factor opportunity scoring (impact, effort, risk). |
| `budget_guard.py` | `python/extensions/` (e.g., `_35_budget_guard.py`) | Monitors token/compute usage; triggers behavior adjustments on overruns. |
| `watchdog.py` | `python/extensions/` (e.g., `_40_watchdog.py`) | Validates outputs, halts workflows on anomalies. |
| `telemetry_push.sh` | `instruments/ops/` | Publishes mission KPIs to shared dashboards. |
| `knowledge_ingest.py` | `instruments/research/` | Normalizes scouting outputs and stores them in `knowledge/custom/main`. |
| `compliance_pack.md` | `docs/policies/` | Canonical policy bundle referenced by Compliance Guardian. |

### Build Steps
1. **Prompts:** Generate persona files using the template in Section 8 and register them in `agent.system.main.md`.
2. **Extensions:** Implement budget guard + watchdog extensions; ensure alphabetical ordering prefixes reflect execution order.
3. **Instruments:** For each department, add at least one instrument that encapsulates its repetitive workflows (scoring, experimentation, deployment, telemetry).
4. **Scheduling:** Use cron or an orchestration agent to run scouting, budgeting, and telemetry instruments on fixed cadences.
5. **Testing:** Dry-run each instrument via `run_cli.py instruments <name>` (or equivalent) before enabling full autonomy.
6. **Observability:** Link telemetry outputs to dashboards accessible from the Web UI for optional human monitoring.

These scaffolds ensure every persona has a dedicated toolkit, observability path, and safety net, reinforcing the low-touch operation goal.

---

## 11. Immersive Collaboration & Visualization UI

### 11.1 Experience Goals
- **Situational Awareness:** Shared, real-time map of active missions, responsible agents, and workflow state.
- **Low-friction Dialogue:** Zoom-like canvas where agents can “speak,” exchange artifacts, and request clarification without leaving the UI.
- **Replayability:** Session snapshots captured for auditing how decisions were reached.

### 11.2 Interface Zones
1. **Mission Map (left pane):** Node-link graph (missions → departments → agents) with status colors and tooltips containing KPIs + current LLM.
2. **Collaboration Theater (center):** Spatial meeting room:
   - Seats/avatars for participating agents and humans.
   - Avatars display role iconography, provider badge, and live transcript bubble.
   - Shared whiteboard synced to `logs/board_sessions/<timestamp>.json`.
3. **Command Console (right pane):** Action queue (spawn subordinate, run instrument, adjust behavior) and telemetry gauges (budget, risk, throughput).

### 11.3 Interaction Mechanics
- **Agent Speech:** Agents stream updates (text + optional TTS) into bubbles; transcripts saved to `logs/ui_sessions/`.
- **Artifact Docking:** Drag artifacts from the `webui` file browser into the whiteboard; objects reference canonical files to avoid duplication.
- **Planning Templates:** Load pre-built canvases (OKR planner, experiment matrix) via instruments for structured workshops.
- **Moderation Controls:** Apex Orchestrator or sponsor can spotlight speakers, freeze the room, or enforce speaking order.

### 11.4 Implementation Hooks
- Frontend modules (extend `webui/js/`):
  - `agentsGraph.js`: d3-force rendering fed by `/api/missions/graph`.
  - `collabRoom.js`: WebRTC/WebSocket session manager for avatars, chat, and whiteboard diffing.
  - `llmBadges.css`: Visual mapping of model/provider combos.
- Backend additions:
  - Streaming endpoint emitting agent lifecycle events (join, speak, artifact shared).
  - Session controller persisting meeting metadata + board states into `logs/`.

---

## 12. Multi-LLM Strategy Per Role

### 12.1 Assignment Matrix
| Persona | Primary Model | Secondary / Fallback | Notes |
| --- | --- | --- | --- |
| Apex Orchestrator | GPT-4.1 / Claude Opus | GPT-4o mini | Needs long context + governance rigor. |
| Portfolio Navigator | Gemini 1.5 Pro | Claude Sonnet | Balanced analysis vs. cost. |
| Research Fellows | Mixtral 8x22B (API) | Local Llama-3.1-70B | High-parallel experimentation. |
| Product Synthesists | GPT-4o mini | Llama-3.1-70B | UX narratives + storytelling. |
| Compliance Guardian | GPT-4o | Claude Opus | Policy/law precision. |
| Telemetry Sentinel | DeepSeek Coder V2 | Local function-calling model | Data summarization + anomaly detection. |

### 12.2 Routing Logic
- Extension `_15_model_router.py`:
  - Reads persona metadata (stored in persona prompt files or `settings.yml`) to pick `preferred_model`.
  - Checks provider quotas; if usage >80% or latency spikes, switches to fallback.
  - Emits routing decisions to telemetry for monitoring.
- Behavior adjustments can override the router when special handling is needed (e.g., red-team exercises).

### 12.3 Quality & Cost Monitoring
- Every tool call logs: provider, model, input/output tokens, latency, perceived quality score.
- Telemetry Sentinel aggregates per-persona stats and recommends rebalancing (e.g., shift Research Fellows to local models when load is high).
- Budget Guard extension enforces per-department token ceilings; on breach, router downgrades non-critical personas automatically.

---

## 13. Sandbox Collaboration Environment (MVP)

### 13.1 Objectives
1. Validate the immersive UI and multi-LLM routing in isolation.
2. Provide a safe arena for agent-agent-human workshops with synthetic missions.
3. Gather UX + performance telemetry before touching production data.

### 13.2 Sandbox Stack
- **Docker profile `sandbox`:** Launches minimal services + mock integrations.
- **Data:** Synthetic missions, faux knowledge base, isolated memory store at `/sandbox_memory`.
- **Models:** Prefer staged API keys or local open-source models; cap spend via environment variables.
- **Telemetry:** Writes to `logs/sandbox/*` for easy cleanup.

### 13.3 Core Test Scenarios
| Scenario | Description | Success Criteria |
| --- | --- | --- |
| Planning Summit | 5 personas prioritize synthetic roadmap in collab room. | OKR board saved, transcripts archived, no dropped connections. |
| Research Relay | Research Fellow → Product Synthesist → Engineer handoff using whiteboard artifacts. | Artifacts linked, multi-LLM routing recorded. |
| Customer Preview | Simulated client persona joins, receives demo, leaves feedback captured to memory. | Compliance Guardian verifies messaging vs. policy pack. |

### 13.4 Exit Criteria
- Stable WebSocket sessions with ≥6 concurrent avatars.
- Cost telemetry within sandbox budget envelope.
- Guardrail extensions successfully flag injected issues.

---

## 14. Roadmap for Productionizing the UI
1. **Design System:** Extend `webui/css` with a “mission control” palette; ensure WCAG AA contrast.
2. **Graph API:** Implement `/api/missions/graph` with caching + permission checks.
3. **Realtime Backbone:** WebSocket gateway + optional WebRTC audio pipeline for live voice “agent briefings.”
4. **Session Recording:** Serialize transcripts, whiteboard diffs, mission decisions into `logs/ui_sessions/<id>.json` and HTML viewer.
5. **Security Model:** JWT-based roles (sponsor, agent, observer) + per-session PIN for external participants.
6. **Rollout:** Sandbox → staging missions → production; enable customer-facing invites only after telemetry + compliance sign-off.

The UI, multi-LLM routing, and sandbox strategy together enable a testable, graphical collaboration layer where agents and humans coordinate like a virtual R&D control room before expanding to real customer interactions.

---

## 15. Living Documentation & Iterative Improvement Protocol

### 15.1 Continuous Documentation Streams
- **Mission Diaries:** Every active program (e.g., the Autonomous Listing Service) maintains a rolling log in `docs/programs/<mission>/journal.md` capturing decisions, blockers, and outcomes per sprint.
- **Agent Telemetry Snapshots:** Telemetry Sentinel exports weekly health summaries (latency, cost, delegation frequency) into `logs/reports/<week>.md`, feeding performance discussions.
- **Prompt Changelog:** Persona prompt updates are versioned under `prompts/super-agency/CHANGELOG.md`, ensuring traceability between behavioral tweaks and observed results.

### 15.2 Iterative Improvement Loop
1. **Observe:** Collect metrics from mission diaries, telemetry, and customer interactions.
2. **Diagnose:** Portfolio Navigator + relevant Domain Studio review anomalies or opportunities inside the Collaboration Theater.
3. **Design Experiments:** Create improvement hypotheses (e.g., new negotiation playbook for listings) and encode them as:
   - Behavior rule adjustments,
   - Instrument updates,
   - Prompt/Pipeline revisions.
4. **Deploy:** Ship changes through sandbox → staging → production pipeline with automated validation hooks.
5. **Reflect:** Capture outcomes in mission diaries; if successful, promote learnings to `knowledge/custom/main` for reuse.

### 15.3 Cross-Mission Feedback Sharing
- Quarterly **Agency Retrospectives** aggregate insights from all missions, highlighting reusable playbooks (image enhancement steps, pricing heuristics).
- **Improvement Backlog** stored in `docs/agency_improvements.md` ranks cross-cutting enhancements (e.g., better RAG embeddings, refined UI micro-interactions) with designated owner agents.
- **Auto-Watchdogs** detect regressions (e.g., rising unanswered inquiries) and open improvement tasks automatically via behavior adjustment instructions, ensuring the agency self-tunes without waiting for human prompts.

### 15.4 Co-Development with New Services
When launching new services (like the Autonomous Listing Service):
- Embed the mission diary + improvement backlog from day one.
- Reuse the iterative loop above so the service and the core agency evolve together.
- Require each release to document: decision rationale, metrics impacted, and next hypothesis, guaranteeing a living blueprint as the system scales.

This protocol keeps the agency’s documentation synchronized with real operations while institutionalizing an experiment-driven mindset for every new service it incubates.