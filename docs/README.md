![Agent Zero Logo](res/header.png)
# Agent Zero Documentation

- **[Installation](installation.md):** Set up (or [update](installation.md#how-to-update-agent-zero)) Agent Zero on your system.
- **[Usage Guide](usage.md):** Explore GUI features and usage scenarios.
- **[Architecture Overview](architecture.md):** Understand the internal workings of the framework.
- **[Token Compression Protocol](token_compression_protocol.md):** Run the TCP service and integrate it with clients (including browser extensions).
- **[Contributing](contribution.md):** Learn how to contribute to the Agent Zero project.
- **[Troubleshooting and FAQ](troubleshooting.md):** Find answers to common issues and questions.

For architecture and source-linked internals, use
[DeepWiki for Agent Zero](https://deepwiki.com/agent0ai/agent-zero). The local
docs focus on practical setup, screenshots, and user workflows.

## Quick Start

- **[Quickstart Guide](quickstart.md):** Get up and running in 5 minutes with Agent Zero.
- **[Agent Zero Launcher](guides/launcher.md):** Use the desktop app to set up Docker, install Agent Zero, open Instances, or connect a remote Instance.
- **[First-Run Onboarding](guides/onboarding.md):** Choose Cloud, AI account, or Local access, then select main and utility models.
- **[Installation Guide](setup/installation.md):** A0 Launcher downloads, A0 Install, direct Docker, updates, and advanced Docker setup (includes [How to Update](setup/installation.md#how-to-update-agent-zero)).
- **[A0 CLI Connector](guides/a0-cli-connector.md):** Install the host connector for a running Agent Zero instance, use the command palette, and switch Browser modes.
- **[Self Update](guides/self-update.md):** How the in-app updater works (technical reference).
- **[VPS Deployment](setup/vps-deployment.md):** Deploy Agent Zero on a remote server.
- **[Development Setup](setup/dev-setup.md):** Set up a local development environment.

## User Guides

- **[Usage Guide](guides/usage.md):** Practical tour of Agent Zero's main workflows.
- **[Agent Zero Launcher](guides/launcher.md):** Fresh-machine Launcher walkthrough, Docker setup gate, Installs, Instances, and docs screenshot capture with Playwright/Electron.
- **[First-Run Onboarding](guides/onboarding.md):** Set up OpenRouter, our proxy API or another provider with the guided wizard.
- **[Browser Guide](guides/browser.md):** Use the built-in Browser, live Canvas surface, annotations, screenshots, host browser mode, and extensions.
- **[Desktop Guide](guides/desktop.md):** Use the built-in Linux desktop, GUI apps, and LibreOffice Writer/Calc/Impress Cowork.
- **[A0 CLI Connector](guides/a0-cli-connector.md):** Terminal-first host connector for Agent Zero, with screenshots of the host picker, connected shell, command palette, and Browser modes.
- **[Create a Small Plugin](guides/create-plugin.md):** Build and review a tiny Web UI plugin that adds an unread dot to the chat list.
- **[Skills Guide](guides/skills.md):** Open the Skills selector, add active skills, and remove prompt protocol entries you no longer need.
- **[Agent Profiles](guides/agent-profiles.md):** Create and manage profiles in Easy or Advanced mode, set project availability, and control Tool, MCP, and Skill access.
- **[Model Presets](guides/model-presets.md):** Create simple named shortcuts for model setups.
- **[Memory Guide](guides/memory.md):** Search, edit, delete, and curate memories so useful context does not become stale noise.
- **[Projects Tutorial](guides/projects.md):** Learn to create isolated workspaces with dedicated context and memory.
- **[API Integration](guides/api-integration.md):** Add external APIs without writing code.
- **[MCP Setup](guides/mcp-setup.md):** Configure Model Context Protocol servers.
- **[A2A Setup](guides/a2a-setup.md):** Enable agent-to-agent communication.
- **[Troubleshooting](guides/troubleshooting.md):** Solutions to common issues and FAQs.

## Technical Reference

- **[DeepWiki for Agent Zero](https://deepwiki.com/agent0ai/agent-zero):** Architecture, Web UI internals, plugin lifecycle, backend APIs, deployment details, and source-linked explanations.
- **[Architecture](developer/architecture.md):** Short local handoff to DeepWiki plus practical starting points.
- **[Plugins](developer/plugins.md):** Compact plugin starting points and sharing checklist.
- **[Extensions](developer/extensions.md):** Short guide for when an extension is the right tool.
- **[Connectivity](developer/connectivity.md):** Choose between A0 CLI, MCP, A2A, and external APIs.
- **[WebSockets](developer/websockets.md):** Short local handoff to DeepWiki and source files.
- **[MCP Configuration](developer/mcp-configuration.md):** Compact reference for MCP JSON.
- **[Notifications](developer/notifications.md):** Notification system architecture and setup.
- **[Contributing Skills](developer/contributing-skills.md):** Create and share agent skills.
- **[Contributing Guide](guides/contribution.md):** Contribute to the Agent Zero project.

## Community & Support

- **Join the Community:** Connect with other users on [Discord](https://discord.gg/B8KZKNsPpj) to discuss ideas, ask questions, and collaborate.
- **Share Your Work:** Show off your Agent Zero creations and workflows in the [Show and Tell](https://github.com/agent0ai/agent-zero/discussions/categories/show-and-tell) area.
- **Report Issues:** Use the [GitHub issue tracker](https://github.com/agent0ai/agent-zero/issues) to report bugs or suggest features.
- **Follow Updates:** Subscribe to the [YouTube channel](https://www.youtube.com/@AgentZeroFW) for tutorials and release videos.

---

## Table of Contents

- [Welcome to the Agent Zero Documentation](#agent-zero-documentation)
  - [Your Experience with Agent Zero](#your-experience-with-agent-zero-starts-now)
  - [Table of Contents](#table-of-contents)
- [Installation Guide](installation.md)
  - [Windows, macOS and Linux Setup](installation.md#windows-macos-and-linux-setup-guide)
  - [Settings Configuration](installation.md#settings-configuration)
  - [Choosing Your LLMs](installation.md#choosing-your-llms)
  - [Installing and Using Ollama](installation.md#installing-and-using-ollama-local-models)
  - [Using Agent Zero on Mobile](installation.md#using-agent-zero-on-your-mobile-device)
  - [How to Update Agent Zero](installation.md#how-to-update-agent-zero)
  - [Full Binaries Installation](installation.md#in-depth-guide-for-full-binaries-installation)
- [Usage Guide](usage.md)
  - [Basic Operations](usage.md#basic-operations)
    - [Restart Framework](usage.md#restart-framework)
    - [Action Buttons](usage.md#action-buttons)
    - [File Attachments](usage.md#file-attachments)
  - [Tool Usage](usage.md#tool-usage)
  - [Example of Tools Usage](usage.md#example-of-tools-usage-web-search-and-code-execution)
  - [Multi-Agent Cooperation](usage.md#multi-agent-cooperation)
  - [Prompt Engineering](usage.md#prompt-engineering)
  - [Voice Interface](usage.md#voice-interface)
  - [Mathematical Expressions](usage.md#mathematical-expressions)
  - [File Browser](usage.md#file-browser)
- [Architecture Overview](architecture.md)
  - [System Architecture](architecture.md#system-architecture)
  - [Runtime Architecture](architecture.md#runtime-architecture)
  - [Implementation Details](architecture.md#implementation-details)
  - [Core Components](architecture.md#core-components)
    - [Agents](architecture.md#1-agents)
    - [Tools](architecture.md#2-tools)
    - [SearXNG Integration](architecture.md#searxng-integration)
    - [Memory System](architecture.md#3-memory-system)
    - [Messages History and Summarization](archicture.md#messages-history-and-summarization)
    - [Prompts](architecture.md#4-prompts)
    - [Knowledge](architecture.md#5-knowledge)
    - [Instruments](architecture.md#6-instruments)
    - [Extensions](architecture.md#7-extensions)
  - [Contributing](contribution.md)
  - [Getting Started](contribution.md#getting-started)
  - [Making Changes](contribution.md#making-changes)
  - [Submitting a Pull Request](contribution.md#submitting-a-pull-request)
  - [Documentation Stack](contribution.md#documentation-stack)
- [Token Compression Protocol](token_compression_protocol.md)
- [Troubleshooting and FAQ](troubleshooting.md)
  - [Frequently Asked Questions](troubleshooting.md#frequently-asked-questions)
  - [Troubleshooting](troubleshooting.md#troubleshooting)
