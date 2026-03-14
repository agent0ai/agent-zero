# Agent Jumbo: Platform & Services Documentation

## 1. Executive Overview

Agent Jumbo is a multi-agent autonomous framework designed for high-assurance tasks, workflow automation, and professional integration. It leverages a hierarchical agent architecture ("Agent 0") to delegate specialized work to subordinate agents like 'Developer', 'Researcher', and 'Hacker'.

---

## 2. Core Architecture & Runtime

### 🔄 Agent Execution Loop

* **Implementation**: `agent.py`
* **Functionality**: Manages the main monologue loop, tool extraction, and context windowing.
* **Contexts**: Supports `USER`, `TASK`, and `BACKGROUND` contexts stored in `AgentContext`.
* **Hierarchy**: Subordinate agents are initialized with a `_superior` link to allow recursive task escalation.

### 🧭 LLM Router & Model Management

* **Implementation**: `python/helpers/llm_router.py`, `models.py`
* **Functionality**: An abstraction layer that routes tasks to different providers (Anthropic, OpenAI, Ollama) based on required capabilities (Reasoning, Speed, Vision).
* **Failover**: Automatically falls back from cloud endpoints to local Ollama instances if specific rules are met.

### 🧠 Knowledge & Memory (RAG)

* **Implementation**: `python/helpers/memory/`, `python/helpers/knowledge/`
* **Functionality**:
  * **Short-term**: Managed via chat history summarization.
  * **Long-term**: FAISS-based vector search for codebase and document retrieval.

---

## 3. Specialized Integration Services

### 📧 Gmail & Email Hub

* **Implementation**: `python/api/gmail_oauth_*.py`, `python/helpers/gmail_helper.py`
* **Functionality**: Secure OAuth2-based email management, automated triage, and attachment handling.

### 🔌 Model Context Protocol (MCP)

* **Implementation**: `python/helpers/mcp_handler.py`
* **Functionality**: Standardized tool integration via SSE, Stdio, or HTTP. Allows Agent Jumbo to consume tools from the global MCP ecosystem.

### 📈 Workflow Engine

* **Implementation**: `instruments/custom/workflow_engine/`
* **Functionality**: Manages long-running business processes through a 5-level proficiency ladder. Includes visual dependency graph generation (Mermaid).

---

## 4. Mobile-First Security Hub (New)

### 🔒 Identity (Passkeys)

* **Implementation**: `python/helpers/passkey_vault.py`
* **Technology**: WebAuthn/FIDO2. Hardware-bound biometric signatures for high-risk tools.

### 🛡️ Sentinels & Protections

* **Implementation**: `python/helpers/security.py`
* **Traffic Sentinel**: Auto-locks agent if $>15$ actions/min (Anomaly detection).
* **Network Sentinel**: Intercepts unauthorized outbound network calls.
* **Zero-Knowledge Vault**: AES-256-GCM encryption for all data at rest.

### 📱 Proactive Push (VAPID)

* **Implementation**: `python/helpers/proactive.py`
* **Functionality**: Actionable mobile notifications for remote tool approval and device telemetry monitoring.

---

## 5. Operations & UI

### 🚀 Web Interface & PWA

* **Implementation**: `webui/index.html`, `webui/js/sw.js`
* **Frontend**: Alpine.js-powered real-time sync with the agent loop.
* **Mobile**: Installable PWA with background push support.

### 🗓️ Scheduler & Backups

* **Implementation**: `python/api/scheduler_*.py`, `python/api/backup_*.py`
* **Functionality**: Automated snapshots of the work directory and periodic task execution.

---

## 6. Developer Reference

* **API Path**: `/api/` (Requires X-API-KEY or Session)
* **Logs**: `logs/`
* **Configuration**: `.env`, `mcp_config_claude.json`, `conf/model_providers.yaml`
