<div align="center">

# `Apollos AI`

> Fork of [agent0ai/agent-zero](https://github.com/agent0ai/agent-zero), maintained at [jrmatherly/apollos-ai](https://github.com/jrmatherly/apollos-ai).

## Documentation:

[Introduction](#a-personal-organic-agentic-framework-that-grows-and-learns-with-you) •
[Installation](./docs/setup/installation.md) •
[How to update](./docs/setup/installation.md#how-to-update-apollos-ai) <br>
[Development Setup](./docs/setup/dev-setup.md) •
[Usage](./docs/guides/usage.md)

Or see DeepWiki generated documentation:

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/jrmatherly/apollos-ai)

</div>

<div align="center">

> ### 🚨 **APOLLOS AI SKILLS** 🚨
> **Skills System** - portable, structured agent capabilities using the open `SKILL.md` standard (compatible with Claude Code, Codex and more).
>
> **Plus:** Git-based Projects with authentication for public/private repositories - clone codebases directly into isolated workspaces.
>
> See [Usage Guide](./docs/guides/usage.md) and [Projects Tutorial](./docs/guides/projects.md) to get started.
</div>

[![Showcase](/docs/res/showcase-thumb.png)](https://youtu.be/lazLNcEYsiQ)

## A personal, organic agentic framework that grows and learns with you

- Apollos AI is not a predefined agentic framework. It is designed to be dynamic, organically growing, and learning as you use it.
- Apollos AI is fully transparent, readable, comprehensible, customizable, and interactive.
- Apollos AI uses the computer as a tool to accomplish its (your) tasks.

# ⚙️ Installation

Click to open a video to learn how to install Apollos AI:

[![Easy Installation guide](/docs/res/easy_ins_vid.png)](https://www.youtube.com/watch?v=w5v5Kjx51hs)

A detailed setup guide for Windows, macOS, and Linux with a video can be found in the Apollos AI Documentation at [this page](./docs/setup/installation.md).

### ⚡ Quick Start

```bash
# Pull and run with Docker

docker pull ghcr.io/jrmatherly/apollos-ai
docker run -p 50001:80 ghcr.io/jrmatherly/apollos-ai

# Visit http://localhost:50001 to start
```

# 💡 Key Features

1. **General-purpose Assistant**

- Apollos AI is not pre-programmed for specific tasks (but can be). It is meant to be a general-purpose personal assistant. Give it a task, and it will gather information, execute commands and code, cooperate with other agent instances, and do its best to accomplish it.
- It has a persistent memory, allowing it to memorize previous solutions, code, facts, instructions, etc., to solve tasks faster and more reliably in the future.

![Agent 0 Working](/docs/res/ui_screen2.png)

2. **Computer as a Tool**

- Apollos AI uses the operating system as a tool to accomplish its tasks. It has no single-purpose tools pre-programmed. Instead, it can write its own code and use the terminal to create and use its own tools as needed.
- The only default tools in its arsenal are online search, memory features, communication (with the user and other agents), and code/terminal execution. Everything else is created by the agent itself or can be extended by the user.
- Tool usage functionality has been developed from scratch to be the most compatible and reliable, even with very small models.
- **Default Tools:** Apollos AI includes tools like knowledge, code execution, and communication.
- **Creating Custom Tools:** Extend Apollos AI's functionality by creating your own custom tools.
- **Skills (SKILL.md Standard):** Skills are contextual expertise loaded dynamically when relevant. They use the open SKILL.md standard (developed by Anthropic), making them compatible with Claude Code, Cursor, Goose, OpenAI Codex CLI, and GitHub Copilot.

3. **Multi-agent Cooperation**

- Every agent has a superior agent giving it tasks and instructions. Every agent then reports back to its superior.
- In the case of the first agent in the chain (Agent 0), the superior is the human user; the agent sees no difference.
- Every agent can create its subordinate agent to help break down and solve subtasks. This helps all agents keep their context clean and focused.

![Multi-agent](docs/res/usage/multi-agent.png)

4. **Completely Customizable and Extensible**

- Almost nothing in this framework is hard-coded. Nothing is hidden. Everything can be extended or changed by the user.
- The whole behavior is defined by a system prompt in the **prompts/default/agent.system.md** file. Change this prompt and change the framework dramatically.
- The framework does not guide or limit the agent in any way. There are no hard-coded rails that agents have to follow.
- Every prompt, every small message template sent to the agent in its communication loop can be found in the **prompts/** folder and changed.
- Every default tool can be found in the **python/tools/** folder and changed or copied to create new predefined tools.
- **Automated configuration** via `A0_SET_` environment variables for deployment automation and easy setup.

![Prompts](/docs/res/profiles.png)

5. **Communication is Key**

- Give your agent a proper system prompt and instructions, and it can do miracles.
- Agents can communicate with their superiors and subordinates, asking questions, giving instructions, and providing guidance. Instruct your agents in the system prompt on how to communicate effectively.
- The terminal interface is real-time streamed and interactive. You can stop and intervene at any point. If you see your agent heading in the wrong direction, just stop and tell it right away.
- There is a lot of freedom in this framework. You can instruct your agents to regularly report back to superiors asking for permission to continue. You can instruct them to use point-scoring systems when deciding when to delegate subtasks. Superiors can double-check subordinates' results and dispute. The possibilities are endless.

## 🚀 Real-world use cases

- **Financial Analysis & Charting** - `"Find last month's Bitcoin/USD price trend, correlate with major cryptocurrency news events, generate annotated chart with highlighted key dates"`

- **Excel Automation Pipeline** - `"Scan incoming directory for financial spreadsheets, validate and clean data, consolidate from multiple sources, generate executive reports with flagged anomalies"`

- **API Integration Without Code** - `"Use this Google Gemini API snippet to generate product images, remember the integration for future use"` - agent learns and stores the solution in memory

- **Automated Server Monitoring** - `"Check server status every 30 minutes: CPU usage, disk space, memory. Alert if metrics exceed thresholds"` (scheduled task with project-scoped credentials)

- **Multi-Client Project Isolation** - Separate projects for each client with isolated memory, custom instructions, and dedicated secrets - prevents context bleed across sensitive work

## 🐳 Fully Dockerized, with Speech-to-Text and TTS

![Settings](docs/res/settings-page-ui1.png)

- Customizable settings allow users to tailor the agent's behavior and responses to their needs.
- The Web UI output is very clean, fluid, colorful, readable, and interactive; nothing is hidden.
- You can load or save chats directly within the Web UI.
- The same output you see in the terminal is automatically saved to an HTML file in **logs/** folder for every session.

![Time example](/docs/res/time_example.jpg)

- Agent output is streamed in real-time, allowing users to read along and intervene at any time.
- No coding is required; only prompting and communication skills are necessary.
- With a solid system prompt, the framework is reliable even with small models, including precise tool usage.

## 👀 Keep in Mind

1. **Apollos AI Can Be Dangerous!**

- With proper instruction, Apollos AI is capable of many things, even potentially dangerous actions concerning your computer, data, or accounts. Always run Apollos AI in an isolated environment (like Docker) and be careful what you wish for.

2. **Apollos AI Is Prompt-based.**

- The whole framework is guided by the **prompts/** folder. Agent guidelines, tool instructions, messages, utility AI functions, it's all there.

## 📚 Read the Documentation

| Page | Description |
|-------|-------------|
| [Installation](./docs/setup/installation.md) | Installation, setup and configuration |
| [Usage](./docs/guides/usage.md) | Basic and advanced usage |
| [Guides](./docs/guides/) | Step-by-step guides: Usage, Projects, API Integration, MCP Setup, A2A Setup |
| [Development Setup](./docs/setup/dev-setup.md) | Development and customization |
| [WebSocket Infrastructure](./docs/developer/websockets.md) | Real-time WebSocket handlers, client APIs, filtering semantics, envelopes |
| [Extensions](./docs/developer/extensions.md) | Extending Apollos AI |
| [Connectivity](./docs/developer/connectivity.md) | External API endpoints, MCP server connections, A2A protocol |
| [Architecture](./docs/developer/architecture.md) | System design and components |
| [Contributing](./docs/guides/contribution.md) | How to contribute |
| [Troubleshooting](./docs/guides/troubleshooting.md) | Common issues and their solutions |

## 🎯 Changelog

### v0.9.8 - Skills, UI Redesign & Git projects
[Release video](https://youtu.be/NV7s78yn6DY)

- Skills
  - Skills System replacing the legacy Instruments with a new `SKILL.md` standard for structured, portable agent capabilities.
  - Built-in skills, and UI support for importing and listing skills
- Real-time WebSocket infrastructure replacing the polling-based approach for UI state synchronization
- UI Redesign
  - Process groups to visually group agent actions with expand/collapse support
  - Timestamps, steps count and execution time with tool-specific badges
  - Step detail modals with key-value and raw JSON display
  - Collapsible responses with show more/less and copy buttons on code blocks and tables
  - Message queue system allowing users to queue messages while the agent is still processing
  - In-browser file editor for viewing and editing files without leaving the UI
  - Welcome screen redesign with info and warning banners for connection security, missing API keys, and system resources
  - Scheduler redesign with standalone modal, separate task list, detail and editor components, and project support
  - Smooth response rendering and scroll stabilization across chat, terminals, and image viewer
  - Chat width setting and reworked preferences panel
  - Image viewer improvements with scroll support and expanded viewer
  - Redesigned sidebar with reusable dropdown component and streamlined buttons
  - Inline button confirmations for critical actions
  - Improved login design and new logout button
  - File browser enhanced with rename and file actions dropdown
- Git projects
  - Git-based projects with clone authentication for public and private repositories
- Four new LLM providers: CometAPI, Z.AI, Moonshot AI, and AWS Bedrock
- Microsoft Dev Tunnels integration for secure remote access
- User data migration to `/usr` directory for cleaner separation of user and system files
- Subagents system with configurable agent profiles for different roles
- Memory operations offloaded to deferred tasks for better performance
- Environment variables can now configure settings via `A0_SET_*` prefix in `.env`
- Automatic migration with overwrite support for `.env`, scheduler, knowledge, and legacy directories
- Projects support extended to MCP, A2A, and external API
- Workdir outside project support for more flexible file organization
- Agent number tracking in backend and responses for multi-agent identification
- Many bug fixes and stability improvements across the UI, MCP tools, scheduler, uploads, and WebSocket handling

### v0.9.7 - Projects
[Release video](https://youtu.be/RrTDp_v9V1c)
- Projects management
  - Support for custom instructions
  - Integration with memory, knowledge, files
  - Project specific secrets
- New Welcome screen/Dashboard
- New Wait tool
- Subordinate agent configuration override support
- Support for multiple documents at once in document_query_tool
- Improved context on interventions
- Openrouter embedding support
- Frontend components refactor and polishing
- SSH metadata output fix
- Support for windows powershell in local TTY utility
- More efficient selective streaming for LLMs
- UI output length limit improvements

### v0.9.6 - Memory Dashboard
[Release video](https://youtu.be/sizjAq2-d9s)
- Memory Management Dashboard
- Kali update
- Python update + dual installation
- Browser Use update
- New login screen
- LiteLLM retry on temporary errors
- Github Copilot provider support

### v0.9.5 - Secrets
[Release video](https://www.youtube.com/watch?v=VqxUdt7pjd8)
- Secrets management - agent can use credentials without seeing them
- Agent can copy paste messages and files without rewriting them
- LiteLLM global configuration field
- Custom HTTP headers field for browser agent
- Progressive web app support
- Extra model params support for JSON
- Short IDs for files and memories to prevent LLM errors
- Tunnel component frontend rework
- Fix for timezone change bug
- Notifications z-index fix

### v0.9.4 - Connectivity, UI
[Release video](https://www.youtube.com/watch?v=C2BAdDOduIc)
- External API endpoints
- Streamable HTTP MCP A0 server
- A2A (Agent to Agent) protocol - server+client
- New notifications system
- New local terminal interface for stability
- Rate limiter integration to models
- Delayed memory recall
- Smarter autoscrolling in UI
- Action buttons in messages
- Multiple API keys support
- Download streaming
- Tunnel URL QR code
- Internal fixes and optimizations

### v0.9.3 - Subordinates, memory, providers Latest
[Release video](https://www.youtube.com/watch?v=-LfejFWL34k)
- Faster startup/restart
- Subordinate agents can have dedicated prompts, tools and system extensions
- Streamable HTTP MCP server support
- Memory loading enhanced by AI filter
- Memory AI consolidation when saving memories
- Auto memory system configuration in settings
- LLM providers available are set by providers.yaml configuration file
- Venice.ai LLM provider supported
- Initial agent message for user + as example for LLM
- Docker build support for local images
- File browser fix

### v0.9.2 - Kokoro TTS, Attachments
[Release video](https://www.youtube.com/watch?v=sPot_CAX62I)

- Kokoro text-to-speech integration
- New message attachments system
- Minor updates: log truncation, hyperlink targets, component examples, api cleanup

### v0.9.1 - LiteLLM, UI improvements
[Release video](https://youtu.be/crwr0M4Spcg)
- Langchain replaced with LiteLLM
  - Support for reasoning models streaming
  - Support for more providers
  - Openrouter set as default instead of OpenAI
- UI improvements
  - New message grouping system
  - Communication smoother and more efficient
  - Collapsible messages by type
  - Code execution tool output improved
  - Tables and code blocks scrollable
  - More space efficient on mobile
- Streamable HTTP MCP servers support
- LLM API URL added to models config for Azure, local and custom providers

### v0.9.0 - Agent roles, backup/restore
[Release video](https://www.youtube.com/watch?v=rMIe-TC6H-k)
- subordinate agents can use prompt profiles for different roles
- backup/restore functionality for easier upgrades
- security and bug fixes

### v0.8.7 - Formatting, Document RAG Latest
[Release video](https://youtu.be/OQJkfofYbus)
- markdown rendering in responses
- live response rendering
- document Q&A tool

### v0.8.6 - Merge and update
[Release video](https://youtu.be/l0qpK3Wt65A)
- Merge with Hacking Edition
- browser-use upgrade and integration re-work
- tunnel provider switch

### v0.8.5 - **MCP Server + Client**
[Release video](https://youtu.be/pM5f4Vz3_IQ)

- Apollos AI can now act as MCP Server
- Apollos AI can use external MCP servers as tools

### v0.8.4.1 - 2
Default models set to gpt-4.1
- Code execution tool improvements
- Browser agent improvements
- Memory improvements
- Various bugfixes related to context management
- Message formatting improvements
- Scheduler improvements
- New model provider
- Input tool fix
- Compatibility and stability improvements

### v0.8.4
[Release video](https://youtu.be/QBh_h_D_E24)

- **Remote access (mobile)**

### v0.8.3.1
[Release video](https://youtu.be/AGNpQ3_GxFQ)

- **Automatic embedding**

### v0.8.3
[Release video](https://youtu.be/bPIZo0poalY)

- ***Planning and scheduling***

### v0.8.2
[Release video](https://youtu.be/xMUNynQ9x6Y)

- **Multitasking in terminal**
- **Chat names**

### v0.8.1
[Release video](https://youtu.be/quv145buW74)

- **Browser Agent**
- **UX Improvements**

### v0.8
[Release video](https://youtu.be/cHDCCSr1YRI)

- **Docker Runtime**
- **New Messages History and Summarization System**
- **Agent Behavior Change and Management**
- **Text-to-Speech (TTS) and Speech-to-Text (STT)**
- **Settings Page in Web UI**
- **SearXNG Integration Replacing Perplexity + DuckDuckGo**
- **File Browser Functionality**
- **KaTeX Math Visualization Support**
- **In-chat File Attachments**

### v0.7
[Release video](https://youtu.be/U_Gl0NPalKA)

- **Automatic Memory**
- **UI Improvements**
- **Instruments**
- **Extensions Framework**
- **Reflection Prompts**
- **Bug Fixes**

## 🤝 Community and Support

- [Report Issues](https://github.com/jrmatherly/apollos-ai/issues) for bug fixes and features
