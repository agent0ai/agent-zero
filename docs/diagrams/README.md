# Agent Jumbo Architecture Diagrams

This directory contains Draw.io diagrams documenting the Agent Jumbo system architecture. These files can be opened in:

- [Draw.io Desktop App](https://www.drawio.com/)
- [Draw.io Web](https://app.diagrams.net/)
- VS Code with the Draw.io Extension

## Available Diagrams

### 1. System Architecture (`system-architecture.drawio`)

**High-level overview of the entire Agent Jumbo system**

- **Web UI Layer**: Alpine.js components, dashboards, settings modal
- **API Layer**: 82 endpoints organized by domain
- **Agent Core Layer**: AgentContext, Agent, LiteLLM, Extensions
- **Instruments Layer**: 17 custom modules (workflow_engine, ralph_loop, etc.)
- **External Services**: Ollama, Anthropic, OpenAI, Gmail, MCP Servers

### 2. Workflow Engine (`workflow-engine.drawio`)

**Detailed architecture of the workflow management system**

- **Tool Layer**: workflow_engine.py (18 actions), workflow_training.py
- **Manager Layer**: WorkflowManager, WorkflowDatabase, WorkflowVisualizer
- **Database Schema**: workflows, executions, stage_progress, tasks, skills tables
- **Stage Lifecycle**: design → poc → mvp → production → support → upgrade
- **API Endpoints**: /workflow_dashboard, /workflow_engine_api, etc.

### 3. Cowork System (`cowork-system.drawio`)

**Collaborative approval framework for tool execution**

- **Core Components**: Fingerprinting, Path Extraction, Approval Check
- **API Endpoints**: /cowork_approvals_list, /cowork_approvals_update, /cowork_folders_*
- **Extension Hook**: _20_cowork_approvals.py (intercepts tool execution)
- **Data Structure**: Approval object schema with status lifecycle
- **Flow Sequence**: 8-step approval workflow visualization

### 4. Ralph Loop (`ralph-loop.drawio`)

**Autonomous iterative task execution system**

- **Concept**: "Ralph Wiggum Technique" - continuous execution until completion
- **Components**: RalphLoopTool (12 actions), RalphLoopManager, RalphLoopDatabase
- **Database Schema**: ralph_loops, ralph_iterations tables
- **Extension Hook**: _85_ralph_loop_check.py (continuation logic)
- **Execution Flow**: Loop lifecycle from start to completion

### 5. Web UI Architecture (`web-ui-architecture.drawio`)

**Alpine.js based reactive interface structure**

- **Main Layout**: Left Panel (sidebar), Right Panel (chat + dashboards)
- **Component Structure**: 66 components in sidebar/, chat/, modals/, panels/, tiles/
- **Settings Modal**: 14 sections for configuration
- **Alpine.js Stores**: 31 stores for state management
- **Vendor Libraries**: Alpine.js, Mermaid, Marked, KaTeX, Flatpickr

### 6. Message Flow (`message-flow.drawio`)

**Agent monologue pipeline for message processing**

- **Input → API → Context**: User message to AgentContext
- **Message Loop**: Iterative prompt building, LLM calls, tool execution
- **Extension Hooks**: monologue_start, message_loop_*, tool_execute_*
- **Tool Execution**: before → execute → after with cowork/telemetry
- **Response**: Output to client via messages.js

## How to Open

### Draw.io Web

1. Go to <https://app.diagrams.net/>
2. Click "Open Existing Diagram"
3. Select the .drawio file

### Draw.io Desktop

1. Download from <https://www.drawio.com/>
2. File → Open → Select .drawio file

### VS Code Extension

1. Install "Draw.io Integration" extension
2. Open any .drawio file directly in VS Code

## Editing Guidelines

- Keep consistent color coding (see legend in each diagram)
- Update diagrams when architecture changes
- Export PNG/SVG versions for documentation if needed
- Test file opens correctly after saving

## Color Legend (consistent across diagrams)

| Color | Meaning |
|-------|---------|
| Green (#d4edda) | Input/Output, Success states |
| Blue (#dae8fc) | Web UI, API layers |
| Cyan (#b0e3e6) | Agent Core, Core Logic |
| Orange (#ffe6cc) | Processing, Context |
| Yellow (#fff2cc) | Tools, Decisions, Loop body |
| Red (#f8cecc) | LLM calls, Database tables, Blocked |
| Purple (#e1d5e7) | Extensions, Hooks |
| Gray (#f5f5f5) | Background containers |
