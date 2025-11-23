# Agent Zero Project Overview

## Purpose
Agent Zero is a personal, organic agentic framework that grows and learns with you. It's designed to be:
- A general-purpose AI assistant that uses the computer as a tool
- Dynamic and organically growing, not a predefined framework
- Fully transparent, customizable, and interactive
- Capable of multi-agent cooperation with hierarchical task delegation

## Key Features
1. **General-purpose Assistant**: Not pre-programmed for specific tasks, but learns and adapts
2. **Computer as a Tool**: Uses the OS to create and execute its own tools via terminal/code
3. **Multi-agent Cooperation**: Hierarchical structure where agents delegate tasks to subordinates
4. **Completely Customizable**: Everything can be modified - prompts, tools, behavior
5. **Communication is Key**: Real-time interactive terminal with user intervention capability

## Architecture Components
- **Agents**: Core actors that receive instructions, reason, and use tools
- **Tools**: Default tools include search, memory, communication, and code/terminal execution
- **Extensions**: Modular extensions for additional functionality
- **Instruments**: Custom functions and procedures that can be called
- **Memory**: Persistent memory for storing solutions, code, facts, instructions
- **Knowledge Base**: FAISS-based vector database for document storage
- **Projects**: Isolated workspaces with their own prompts, files, memory, and secrets

## Runtime Architecture
- Primarily runs in Docker containers for consistency and security
- Web UI runs on port 5000 (configurable via WEB_UI_PORT)
- Supports both Docker runtime and direct host system execution (with RFC configuration)
- Container-based approach ensures consistent environment across platforms