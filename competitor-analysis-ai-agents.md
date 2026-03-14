# AI Agent Frameworks: Competitive Landscape Analysis (March 2026)

## Summary Comparison Table

| Project | GitHub Stars | Language/Stack | Messaging Support | Skills/Tools | Deployment | UI Type | Memory/RAG | Heartbeat/Proactive | Status |
|---------|-------------|---------------|-------------------|-------------|------------|---------|-----------|---------------------|--------|
| **OpenClaw** | ~220K+ | TypeScript/Node.js | WhatsApp, Telegram, Slack, Discord, Signal, iMessage, Teams, Matrix, 50+ channels | 5,700+ (ClawHub registry; 13K+ total) | Docker, local, VPS, cloud container | Web Control UI, WebChat, messaging-native | Markdown-file memory, 12-layer architecture, knowledge graph, semantic search, domain RAG | Yes (30-min default heartbeat, HEARTBEAT.md checklist) | Very Active |
| **AutoGPT** | ~167K | Python | None native | Extensible via plugins/blocks | Docker, local | Web UI (AutoGPT Platform), CLI | Long-term memory via vector stores | No native heartbeat | Active |
| **LangChain** | ~126K | Python, JS/TS | No native (via integrations) | 100+ LLM providers, 50+ vector DBs, 100+ doc formats | pip/npm, Docker, cloud | API/SDK, LangSmith UI | Extensive RAG support, LangGraph state management | No | Very Active |
| **Dify** | ~130K | Python, TypeScript | Via LangBot integration (WeChat, Telegram, Discord, etc.) | 50+ built-in tools | Docker Compose, Kubernetes, AWS AMI | Visual drag-and-drop Web UI | Built-in RAG pipeline, vector DB integration | No native | Very Active |
| **OpenHands** (formerly OpenDevin) | ~65K | Python | Slack, GitHub, GitLab (CI/CD focus) | Code execution, browser, API calls | Docker, cloud, local | Web UI, CLI | Conversation memory | No | Very Active |
| **MetaGPT** | ~64K | Python | None native | SOP-based role workflows | pip, Docker | CLI, API | Shared memory between agents | No | Active |
| **AutoGen** (Microsoft) | ~55K | Python, .NET | None native | Code execution, web browsing, file handling | pip, Docker | AutoGen Studio (Web UI) | Conversation-based memory | No | Maintenance mode (merging into MS Agent Framework) |
| **Open Interpreter** | ~55K | Python | None native | Code execution (Python, JS, Shell), GUI control, vision | Docker (experimental), pip, local | CLI primary, server API | Basic context window | No | Active |
| **CrewAI** | ~45K | Python | Slack (via CrewAI Studio), MCP integrations | 100s of tools, MCP protocol support, Gmail, Teams, Notion, HubSpot, Salesforce | pip, Docker, CrewAI Cloud | Web UI (CrewAI Studio), CLI, API | Short-term, long-term, entity, contextual memory | No native | Very Active |
| **AgentGPT** | ~36K | TypeScript/Python (Next.js + FastAPI) | None | Web search, limited tools | Docker, local (CLI setup) | Web UI (browser-based) | Basic conversation memory | No | Archived (Jan 2026) |
| **LangGraph** | ~24K | Python, JS/TS | No native | Inherits LangChain ecosystem | pip/npm | LangGraph Studio | Stateful graph-based persistence, checkpointing | No | Very Active |
| **BabyAGI** | ~22K | Python | None | Task creation, execution, prioritization | pip, local | CLI only | Pinecone/vector-based task memory | No (but autonomous loop) | Archived/Experimental |
| **Haystack** (deepset) | ~22K | Python | None native | Modular pipeline components, 100+ integrations | pip, Docker | API, deepset Cloud UI | Production-grade RAG, multiple retriever/reader patterns | No | Very Active |
| **SuperAGI** | ~17K | Python | None native | Marketplace-based toolkits (DALL-E, Stable Diffusion, etc.) | Docker | Web UI, API | Long-term memory support | No | Stalled |

---

## Detailed Project Notes

### 1. OpenClaw

- **URL:** [github.com/openclaw/openclaw](https://github.com/openclaw/openclaw)
- **Stars:** ~220K+ (as of early March 2026; grew from 145K in first week of launch, late Jan 2026)
- **Creator:** Peter Steinberger (formerly Clawdbot, Moltbot, Molty)
- **Architecture:** Five-component system: Gateway (message routing, port 18789), Brain (ReAct reasoning loop with LLM), Memory (persistent Markdown files), Skills (plug-in capabilities), Heartbeat (cron-based proactive scheduling). Messaging-native -- the primary interface is through chat platforms, not a web UI.
- **Skills:** 5,700+ curated on ClawHub; 13,729 total in registry as of late Feb 2026; 900+ contributors
- **Messaging:** 50+ channels including WhatsApp, Telegram, Slack, Discord, Signal, iMessage, Google Chat, Microsoft Teams, Matrix, Zalo
- **Deployment:** Self-hosted on laptop, VPS, Mac Mini, or cloud container. Docker is the recommended production method. All data stays local; only LLM inference calls go to provider.
- **Memory/RAG:** 12-layer memory architecture with knowledge graph (3K+ facts), multilingual semantic search (7ms GPU), activation/decay system, domain RAG. Reconstructs itself from files on every boot.
- **Heartbeat:** Runs every 30 minutes by default. Reads HEARTBEAT.md checklist for proactive task monitoring, briefings, reminders.
- **Unique:** Messaging-first design; fastest GitHub star growth in history; consumes 13% of all OpenRouter tokens.

### 2. AutoGPT

- **URL:** [github.com/Significant-Gravitas/AutoGPT](https://github.com/Significant-Gravitas/AutoGPT)
- **Stars:** ~167K
- **Architecture:** Autonomous agent loop: goal decomposition into subtasks, execution, self-evaluation. Uses the Agent Protocol standard (AI Engineer Foundation). AutoGPT Platform provides a visual builder for agent workflows with "blocks" that can be connected.
- **Skills/Tools:** Internet browsing, API access, file I/O, code execution. Extensible block-based system.
- **Messaging:** No native messaging platform support.
- **Deployment:** Docker Compose recommended. Also runs locally.
- **UI:** AutoGPT Platform (web-based builder), CLI for classic mode.
- **Memory:** Long-term memory via vector stores; conversation history persistence.
- **Unique:** First mainstream autonomous agent (April 2023). Pioneer of the "set a goal and let AI work" paradigm.

### 3. LangChain

- **URL:** [github.com/langchain-ai/langchain](https://github.com/langchain-ai/langchain)
- **Stars:** ~126K
- **Architecture:** SDK/framework for building LLM applications. LangGraph (24K stars) provides stateful, graph-based multi-agent orchestration. LangChain core handles integrations and model connectivity.
- **Skills/Tools:** 100+ LLM provider integrations, 50+ vector databases, 100+ document format support. 34.5M monthly downloads (LangGraph).
- **Messaging:** No native chat platform support; used as a building block by other projects.
- **Deployment:** pip/npm packages; LangSmith for observability; LangGraph Cloud for deployment.
- **UI:** LangSmith (observability), LangGraph Studio (development). Primarily API/SDK.
- **Memory:** Comprehensive RAG support. LangGraph provides stateful persistence and checkpointing.
- **Unique:** Dominant ecosystem for LLM application development. Framework of frameworks.

### 4. Dify

- **URL:** [github.com/langgenius/dify](https://github.com/langgenius/dify)
- **Stars:** ~130K
- **Architecture:** Visual workflow builder with agentic AI workflows, RAG pipelines, model management, and observability. Supports LLM Function Calling and ReAct agent patterns.
- **Skills/Tools:** 50+ built-in tools (Google Search, DALL-E, Stable Diffusion, WolframAlpha). Visual drag-and-drop workflow designer.
- **Messaging:** Via LangBot integration for WeChat, Telegram, Discord, and other platforms. Officially documented Dify integration.
- **Deployment:** Docker Compose, Kubernetes (Helm Charts), AWS AMI, Pigsty PostgreSQL stack.
- **UI:** Full visual Web UI with drag-and-drop workflow builder. No-code/low-code approach.
- **Memory/RAG:** Built-in RAG pipeline with vector database integration. Knowledge base management.
- **Unique:** Leading no-code/low-code AI agent platform. Top 100 GitHub project globally. Strong enterprise adoption.

### 5. OpenHands (formerly OpenDevin)

- **URL:** [github.com/OpenHands/OpenHands](https://github.com/OpenHands/OpenHands)
- **Stars:** ~65K
- **Architecture:** AI software development agent. SDK-based composable Python library. Agents can modify code, run commands, browse web, call APIs.
- **Skills/Tools:** Code modification, terminal commands, web browsing, API calls, PR summarization, test generation, documentation.
- **Messaging:** Slack integration, GitHub/GitLab native integrations, CI/CD pipeline integration.
- **Deployment:** Docker, cloud, local. Scalable to 1000s of agents in cloud.
- **UI:** Web UI, CLI, SDK.
- **Memory:** Conversation memory, workspace persistence.
- **Unique:** Purpose-built for software engineering. Strong SWE-bench performance. Enterprise governance support.

### 6. MetaGPT

- **URL:** [github.com/FoundationAgents/MetaGPT](https://github.com/FoundationAgents/MetaGPT)
- **Stars:** ~64K
- **Architecture:** Multi-agent system simulating a software company. Agents assume roles (PM, architect, engineer, etc.) following Standardized Operating Procedures (SOPs). Assembly-line paradigm for task breakdown.
- **Skills/Tools:** SOP-driven workflows. Given one requirement line, produces PRD, design, tasks, and code repository.
- **Messaging:** None native.
- **Deployment:** pip, Docker.
- **UI:** CLI, API. MGX (MetaGPT X) launched Feb 2025 as a natural language programming product.
- **Memory:** Shared memory between agent roles within a project context.
- **Unique:** Software company simulation. Academic paper backing (ICLR). SOP-encoded prompt sequences.

### 7. AutoGen (Microsoft)

- **URL:** [github.com/microsoft/autogen](https://github.com/microsoft/autogen)
- **Stars:** ~55K
- **Architecture:** Multi-agent conversation framework. Agents communicate to solve tasks with human-in-the-loop options. Magentic-One is a state-of-the-art multi-agent team for web browsing, code execution, and file handling.
- **Skills/Tools:** Code execution, web browsing, file handling. Extensible tool system.
- **Messaging:** None native.
- **Deployment:** pip, Docker.
- **UI:** AutoGen Studio (web UI for visual agent creation).
- **Memory:** Conversation-based memory between agents.
- **Status:** Now in maintenance mode. Merging with Semantic Kernel into Microsoft Agent Framework (GA targeted Q1 2026).
- **Unique:** Microsoft backing. Strong research foundation. Merging into enterprise-grade unified framework.

### 8. CrewAI

- **URL:** [github.com/crewAIInc/crewAI](https://github.com/crewAIInc/crewAI)
- **Stars:** ~45K
- **Architecture:** Role-playing autonomous AI agents with collaborative intelligence. Combines Crews (autonomy) and Flows (precision). Deep customization of workflows, prompts, and agent behaviors.
- **Skills/Tools:** 100s of open-source tools. MCP protocol support for thousands of community MCP server tools. Integrations: Gmail, Teams, Notion, HubSpot, Salesforce, Slack.
- **Messaging:** Slack via CrewAI Studio. MCP-based extensibility to other platforms.
- **Deployment:** pip, Docker, CrewAI Cloud (managed).
- **UI:** CrewAI Studio (visual builder), CLI, API.
- **Memory:** Four memory types: short-term, long-term, entity, contextual. Sophisticated memory management.
- **Community:** 100K+ certified developers, 450M+ monthly workflows.
- **Unique:** Role-based agent collaboration. Strong enterprise traction. Four-layer memory system.

### 9. AgentGPT

- **URL:** [github.com/reworkd/AgentGPT](https://github.com/reworkd/AgentGPT)
- **Stars:** ~36K
- **Architecture:** Browser-based agent configuration. Goal-driven: agents autonomously plan sub-tasks and iterate. Stack: Next.js frontend + FastAPI backend + MySQL.
- **Skills/Tools:** Web search (preview), basic task execution.
- **Messaging:** None.
- **Deployment:** CLI-based setup (env vars, DB, backend, frontend). Docker.
- **UI:** Web UI (browser-based agent configuration).
- **Status:** Archived January 28, 2026. Read-only. Reworkd team pivoted to web automation platform.
- **Unique:** Lowest barrier to entry for autonomous agents. i18n support (~20 languages). Agent pause/resume.

### 10. Open Interpreter

- **URL:** [github.com/openinterpreter/open-interpreter](https://github.com/openinterpreter/open-interpreter)
- **Stars:** ~55K
- **Architecture:** Natural language interface for computers. Equips function-calling LLMs with exec() for code execution. Supports Python, JavaScript, Shell, and AppleScript. GUI control and vision capabilities.
- **Skills/Tools:** Code execution across multiple languages, GUI automation, vision/image analysis, screenpipe integration.
- **Messaging:** None native.
- **Deployment:** pip install. Docker support experimental. Server mode via FastAPI/Uvicorn.
- **UI:** CLI primary. Server API available. Uses LMC message format (extended OpenAI format).
- **Memory:** Context window based. Smaller windows for lower RAM usage.
- **Unique:** Computer-use agent. Desktop GUI control. Vision capabilities. --os mode powered by Anthropic.

### 11. BabyAGI

- **URL:** [github.com/yoheinakajima/babyagi](https://github.com/yoheinakajima/babyagi)
- **Stars:** ~22K
- **Architecture:** Task-driven autonomous agent. Three core functions: task execution, task creation, task prioritization. Autonomous loop pattern. Latest version (Sept 2024) is a self-building agent framework.
- **Skills/Tools:** Task management via Pinecone/vector stores. Minimal built-in tools.
- **Messaging:** None.
- **Deployment:** Local Python script.
- **UI:** CLI only.
- **Memory:** Pinecone vector store for task memory and results.
- **Status:** Original archived (Sept 2024 snapshot). New experimental self-building version exists.
- **Unique:** Conceptual pioneer of autonomous AI agent loops. Influential despite simplicity.

### 12. Haystack (deepset)

- **URL:** [github.com/deepset-ai/haystack](https://github.com/deepset-ai/haystack)
- **Stars:** ~22K
- **Architecture:** Modular pipeline-based AI orchestration. Explicit control over retrieval, routing, memory, and generation. Agent workflows with pipeline composition.
- **Skills/Tools:** 100+ integrations. Modular components: retrievers, readers, generators, rankers.
- **Messaging:** None native.
- **Deployment:** pip, Docker, deepset Cloud.
- **UI:** API-first. deepset Cloud provides managed UI.
- **Memory/RAG:** Production-grade RAG. Multiple retriever/reader patterns. Built specifically for search and RAG workloads.
- **Unique:** Best-in-class RAG framework. Enterprise production focus. Modular, transparent architecture.

### 13. SuperAGI

- **URL:** [github.com/TransformerOptimus/SuperAGI](https://github.com/TransformerOptimus/SuperAGI)
- **Stars:** ~17K
- **Architecture:** Dev-first autonomous agent framework. Sequential instruction workflows. Public APIs for agent lifecycle management.
- **Skills/Tools:** SuperAGI Marketplace with toolkits (DALL-E, Stable Diffusion, etc.). HuggingFace and Replicate integration.
- **Messaging:** None native.
- **Deployment:** Docker, web version (app.superagi.com).
- **UI:** Web UI, API.
- **Memory:** Long-term memory support.
- **Status:** Stalled as of 2026. Development spiked mid-2023, minimal activity since. Security vulnerabilities reported.
- **Unique:** Marketplace model for agent toolkits. Public APIs for agent management.

---

## Notable Emerging Competitors (10K+ stars or significant traction)

| Project | Stars | Notes |
|---------|-------|-------|
| **LangGraph** | ~24K | LangChain's stateful multi-agent graph framework. Production standard. |
| **Google ADK** | ~17K | Google's Agent Development Kit. Directed graph workflows. |
| **OpenAI Agents SDK** | New | Official OpenAI agent framework. Growing rapidly. |
| **Vercel AI SDK** | ~15K+ | TypeScript-first AI SDK with agent capabilities. |
| **Mastra** | Emerging | JS/TS agent framework. |
| **ZeroClaw** | New | Rust-based OpenClaw alternative. 3.4MB binary. Edge-first. |
| **PicoClaw** | New | Go-based ultra-lightweight agent. Under 10MB RAM, runs on RISC-V. |

---

## Key Differentiators: OpenClaw vs. The Field

| Capability | OpenClaw | AutoGPT | LangChain | CrewAI | Dify |
|-----------|----------|---------|-----------|--------|------|
| Messaging-native | 50+ platforms | No | No | Limited (Slack) | Via LangBot |
| Proactive heartbeat | Yes (30-min cron) | No | No | No | No |
| Skill marketplace | ClawHub (5,700+) | Plugin system | Integrations hub | MCP tools | 50+ built-in |
| Self-hosted privacy | Full local | Docker | Library | Cloud option | Docker/K8s |
| Memory persistence | 12-layer, cross-session | Vector store | LangGraph state | 4-type memory | RAG pipeline |
| No-code setup | Messaging-first | Web builder | Code-required | Studio UI | Visual builder |
| Star growth rate | Fastest in GitHub history | Mature plateau | Steady growth | Rapid growth | Very strong |

---

## Sources

- [AutoGPT GitHub](https://github.com/Significant-Gravitas/AutoGPT)
- [LangChain GitHub](https://github.com/langchain-ai/langchain)
- [Dify GitHub](https://github.com/langgenius/dify)
- [OpenHands GitHub](https://github.com/OpenHands/OpenHands)
- [MetaGPT GitHub](https://github.com/FoundationAgents/MetaGPT)
- [AutoGen GitHub](https://github.com/microsoft/autogen)
- [CrewAI GitHub](https://github.com/crewAIInc/crewAI)
- [AgentGPT GitHub](https://github.com/reworkd/AgentGPT)
- [Open Interpreter GitHub](https://github.com/openinterpreter/open-interpreter)
- [BabyAGI GitHub](https://github.com/yoheinakajima/babyagi)
- [Haystack GitHub](https://github.com/deepset-ai/haystack)
- [SuperAGI GitHub](https://github.com/TransformerOptimus/SuperAGI)
- [OpenClaw GitHub](https://github.com/openclaw/openclaw)
- [ClawHub Registry](https://clawhub.ai/)
- [Top 10 Most Starred AI Agent Frameworks on GitHub (2026)](https://techwithibrahim.medium.com/top-10-most-starred-ai-agent-frameworks-on-github-2026-df6e760a950b)
- [Top 7 Agentic AI Frameworks in 2026](https://www.alphamatch.ai/blog/top-agentic-ai-frameworks-2026)
- [AI Agent Frameworks Compared (2026)](https://arsum.com/blog/posts/ai-agent-frameworks/)
- [OpenClaw Architecture Overview](https://ppaolo.substack.com/p/openclaw-system-architecture-overview)
- [OpenClaw on CNBC](https://www.cnbc.com/2026/02/02/openclaw-open-source-ai-agent-rise-controversy-clawdbot-moltbot-moltbook.html)
- [OpenClaw Wikipedia](https://en.wikipedia.org/wiki/OpenClaw)
- [Dify 100K Stars Announcement](https://dify.ai/blog/100k-stars-on-github-thank-you-to-our-amazing-open-source-community)
- [Microsoft Agent Framework Overview](https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview)
- [7 Open-Source Frameworks for Deploying AI Bots to Messaging Platforms in 2026](https://aibotbuilder.hashnode.dev/7-open-source-frameworks-for-deploying-ai-bots-to-messaging-platforms-in-2026)
- [Agent Jumbo vs OpenClaw Comparison](https://www.creolestudios.com/agent-jumbo-vs-openclaw/)
- [OpenClaw Skills Guide (DigitalOcean)](https://www.digitalocean.com/resources/articles/what-are-openclaw-skills)
- [OpenClaw Docker Production Guide](https://openclawconsult.com/lab/openclaw-docker)
- [OpenClaw Heartbeat Docs](https://docs.openclaw.ai/gateway/heartbeat)
