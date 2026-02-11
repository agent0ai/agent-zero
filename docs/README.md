![Agent Zero Logo](res/header.png)
# Agent Zero Documentation

Welcome to the Agent Zero documentation hub. Whether you're getting started or diving deep into the framework, you'll find comprehensive guides below.

## Quick Start

- **[Quickstart Guide](quickstart.md):** Get up and running in 5 minutes with Agent Zero.
- **[Installation Guide](setup/installation.md):** Detailed setup instructions for all platforms (or [update your installation](setup/installation.md#how-to-update-agent-zero)).
- **[VPS Deployment](setup/vps-deployment.md):** Deploy Agent Zero on a remote server.
- **[Development Setup](setup/dev-setup.md):** Set up a local development environment.

## User Guides

- **[Usage Guide](guides/usage.md):** Comprehensive guide to Agent Zero's features and capabilities.
- **[Projects Tutorial](guides/projects.md):** Learn to create isolated workspaces with dedicated context and memory.
- **[API Integration](guides/api-integration.md):** Add external APIs without writing code.
- **[MCP Setup](guides/mcp-setup.md):** Configure Model Context Protocol servers.
- **[A2A Setup](guides/a2a-setup.md):** Enable agent-to-agent communication.
- **[Troubleshooting](guides/troubleshooting.md):** Solutions to common issues and FAQs.

## Reference

- **[Environment Variables](reference/environment-variables.md):** Complete catalog of all environment variables, API keys, and settings overrides.
- **[Dependency Management](setup/dependency-management.md):** Adding/removing packages, upstream merge strategy, and Docker compatibility.

## Developer Documentation

- **[Architecture Overview](developer/architecture.md):** Understand Agent Zero's internal structure and components.
- **[Extensions](developer/extensions.md):** Create custom extensions to extend functionality.
- **[Connectivity](developer/connectivity.md):** Connect to Agent Zero from external applications.
- **[WebSockets](developer/websockets.md):** Real-time communication infrastructure.
- **[MCP Configuration](developer/mcp-configuration.md):** Advanced MCP server configuration.
- **[Notifications](developer/notifications.md):** Notification system architecture and setup.
- **[Contributing Skills](developer/contributing-skills.md):** Create and share agent skills.
- **[Contributing Guide](guides/contribution.md):** Contribute to the Agent Zero project.

## Community & Support

- **Join the Community:** Connect with other users on [Discord](https://discord.gg/B8KZKNsPpj) to discuss ideas, ask questions, and collaborate.
- **Share Your Work:** Show off your Agent Zero creations and workflows in the [Show and Tell](https://github.com/jrmatherly/agent-zero/discussions/categories/show-and-tell) area.
- **Report Issues:** Use the [GitHub issue tracker](https://github.com/jrmatherly/agent-zero/issues) to report bugs or suggest features.
- **Follow Updates:** Subscribe to the [YouTube channel](https://www.youtube.com/@AgentZeroFW) for tutorials and release videos.

---

## Table of Contents

- [Quick Start](#quick-start)
  - [Quickstart Guide](quickstart.md)
  - [Installation Guide](setup/installation.md)
    - [Step 1: Install Docker Desktop](setup/installation.md#step-1-install-docker-desktop)
      - [Windows Installation](setup/installation.md#-windows-installation)
      - [macOS Installation](setup/installation.md#-macos-installation)
      - [Linux Installation](setup/installation.md#-linux-installation)
    - [Step 2: Run Agent Zero](setup/installation.md#step-2-run-agent-zero)
      - [Pull Docker Image](setup/installation.md#21-pull-the-agent-zero-docker-image)
      - [Map Folders for Persistence](setup/installation.md#22-optional-map-folders-for-persistence)
      - [Run the Container](setup/installation.md#23-run-the-container)
      - [Access the Web UI](setup/installation.md#24-access-the-web-ui)
    - [Step 3: Configure Agent Zero](setup/installation.md#step-3-configure-agent-zero)
      - [Settings Configuration](setup/installation.md#settings-configuration)
      - [Agent Configuration](setup/installation.md#agent-configuration)
      - [Chat Model Settings](setup/installation.md#chat-model-settings)
      - [API Keys](setup/installation.md#api-keys)
      - [Authentication](setup/installation.md#authentication)
    - [Choosing Your LLMs](setup/installation.md#choosing-your-llms)
    - [Installing Ollama (Local Models)](setup/installation.md#installing-and-using-ollama-local-models)
    - [Using on Mobile Devices](setup/installation.md#using-agent-zero-on-your-mobile-device)
    - [How to Update Agent Zero](setup/installation.md#how-to-update-agent-zero)
  - [VPS Deployment](setup/vps-deployment.md)
  - [Development Setup](setup/dev-setup.md)

- [User Guides](#user-guides)
  - [Usage Guide](guides/usage.md)
    - [Basic Operations](guides/usage.md#basic-operations)
    - [Tool Usage](guides/usage.md#tool-usage)
    - [Projects](guides/usage.md#projects)
      - [What Projects Provide](guides/usage.md#what-projects-provide)
      - [Creating Projects](guides/usage.md#creating-projects)
      - [Project Configuration](guides/usage.md#project-configuration)
      - [Activating Projects](guides/usage.md#activating-projects)
      - [Common Use Cases](guides/usage.md#common-use-cases)
    - [Tasks & Scheduling](guides/usage.md#tasks--scheduling)
      - [Task Types](guides/usage.md#task-types)
      - [Creating Tasks](guides/usage.md#creating-tasks)
      - [Task Configuration](guides/usage.md#task-configuration)
      - [Integration with Projects](guides/usage.md#integration-with-projects)
    - [Secrets & Variables](guides/usage.md#secrets--variables)
    - [Remote Access via Tunneling](guides/usage.md#remote-access-via-tunneling)
    - [Voice Interface](guides/usage.md#voice-interface)
    - [Memory Management](guides/usage.md#memory-management)
    - [Backup & Restore](guides/usage.md#backup--restore)
  - [Projects Tutorial](guides/projects.md)
  - [API Integration](guides/api-integration.md)
  - [MCP Setup](guides/mcp-setup.md)
  - [A2A Setup](guides/a2a-setup.md)
  - [Troubleshooting](guides/troubleshooting.md)

- [Reference](#reference)
  - [Environment Variables](reference/environment-variables.md)

- [Developer Documentation](#developer-documentation)
  - [Architecture Overview](developer/architecture.md)
    - [System Architecture](developer/architecture.md#system-architecture)
    - [Runtime Architecture](developer/architecture.md#runtime-architecture)
    - [Implementation Details](developer/architecture.md#implementation-details)
    - [Core Components](developer/architecture.md#core-components)
      - [Agents](developer/architecture.md#1-agents)
      - [Tools](developer/architecture.md#2-tools)
      - [Memory System](developer/architecture.md#3-memory-system)
      - [Prompts](developer/architecture.md#4-prompts)
      - [Knowledge](developer/architecture.md#5-knowledge)
      - [Skills](developer/architecture.md#6-skills)
      - [Extensions](developer/architecture.md#7-extensions)
  - [Extensions](developer/extensions.md)
  - [Connectivity](developer/connectivity.md)
  - [WebSockets](developer/websockets.md)
  - [MCP Configuration](developer/mcp-configuration.md)
  - [Notifications](developer/notifications.md)
  - [Contributing Skills](developer/contributing-skills.md)
  - [Contributing Guide](guides/contribution.md)

---

### Your journey with Agent Zero starts now!

Ready to dive in? Start with the [Quickstart Guide](quickstart.md) for the fastest path to your first chat, or follow the [Installation Guide](setup/installation.md) for a detailed setup walkthrough.
