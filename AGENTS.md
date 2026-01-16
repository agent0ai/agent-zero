# Agent Zero Skills Manifest

This file defines the core skills available in Agent Zero, following the Anthropic Agent Skills Standard.

Skills defined here are automatically discovered and loaded on-demand when relevant to the agent's current task.

---

## Code Execution

Execute code in a secure sandboxed environment with support for multiple languages and persistent sessions.

**Triggers:** execute code, run script, code execution, terminal, command line, bash, python, shell

Core capability for executing code, running commands, and managing terminal sessions. Supports both local execution and SSH-based remote execution with Docker integration.

---

## Memory Management

Store, retrieve, and manage long-term memories and knowledge.

**Triggers:** remember, recall, memory, save to memory, load memory, knowledge base

Provides persistent memory storage with semantic search capabilities. Allows the agent to remember important information across sessions and recall it when needed.

---

## Knowledge Base Query

Query and search the knowledge base for relevant information.

**Triggers:** search knowledge, query knowledge, find in knowledge, knowledge base, documentation lookup

Advanced knowledge retrieval using vector embeddings and semantic search. Enables the agent to find relevant information from ingested documents and past conversations.

---

## Web Browsing

Browse websites, interact with web pages, and extract information.

**Triggers:** browse, open website, web page, visit url, web scraping, extract from website

Automated web browsing with Playwright integration. Can navigate websites, interact with elements, take screenshots, and extract structured information.

---

## File Management

Read, write, and manage files in the workspace.

**Triggers:** read file, write file, edit file, file system, manage files, create directory

Comprehensive file operations including reading, writing, editing, and organizing files. Supports text files, code files, and binary formats.

---

## Agent Collaboration

Communicate and collaborate with subordinate agents.

**Triggers:** call agent, subordinate agent, delegate task, agent collaboration, multi-agent

Hierarchical agent collaboration system. Allows spawning subordinate agents for specialized tasks and coordinating their work.

---

## Data Analysis

Analyze datasets, perform statistical operations, and generate visualizations.

**Triggers:** analyze data, data analysis, statistics, dataframe, pandas, visualization, chart, graph

Advanced data analysis capabilities using DuckDB and visualization libraries. Can process CSV, Parquet, and JSON data with SQL queries and generate visual reports.

---

## Knowledge Graph

Build and query knowledge graphs from unstructured data.

**Triggers:** knowledge graph, graph database, entities, relationships, graph query, neo4j

Extract entities and relationships from text to build knowledge graphs. Query and visualize complex knowledge structures using graph database operations.

---

## Document Query

Query and extract information from documents using natural language.

**Triggers:** query document, document search, pdf search, document analysis, extract from document

Natural language querying of document contents. Works with PDF, DOCX, TXT, and other document formats using semantic search.

---

## Web Search

Search the web for information using multiple search providers.

**Triggers:** search web, google search, web search, search internet, find online, lookup

Multi-provider web search with DuckDuckGo, Perplexity, and SearXNG support. Retrieves and summarizes web search results.

---

## Browser Agent

Autonomous web browsing with computer-use capabilities.

**Triggers:** browser agent, autonomous browsing, web automation, computer use, browser control

Advanced browser automation using Anthropic's computer-use model. Can autonomously navigate and interact with websites to accomplish complex tasks.

---

## Security Scanning

Scan code for security vulnerabilities and best practices.

**Triggers:** security scan, vulnerability scan, code security, static analysis, security audit

Automated security scanning using tools like Semgrep, Bandit, and Safety. Identifies security vulnerabilities, code smells, and compliance issues.

---

## Git Integration

Interact with Git repositories and manage version control.

**Triggers:** git, commit, push, pull, branch, merge, github, version control

Comprehensive Git operations including commits, branches, merges, and remote operations. Integrates with GitHub, GitLab, and other Git hosting services.

---

## API Integration

Connect to external APIs and services.

**Triggers:** api call, rest api, http request, external service, api integration

Make HTTP requests to external APIs with authentication support. Parse and process API responses for integration with external services.

---

## Schema Generation

Generate schemas and structured data definitions.

**Triggers:** generate schema, json schema, data model, schema definition, type definition

Automatically generate schemas from examples or specifications. Supports JSON Schema, TypeScript types, and Python dataclasses.

---

## Testing & Validation

Run tests and validate code quality.

**Triggers:** run tests, test code, unit test, integration test, validation, code quality

Execute test suites and validate code quality. Supports pytest, unittest, and other testing frameworks.

---

## Performance Profiling

Profile code performance and identify bottlenecks.

**Triggers:** profile code, performance analysis, benchmark, optimize performance, profiling

Analyze code performance using profiling tools. Identify bottlenecks, memory leaks, and optimization opportunities.

---

## Database Operations

Query and manage databases.

**Triggers:** database query, sql, database, query db, data storage, postgres, mysql

Execute database queries and manage database connections. Supports PostgreSQL, MySQL, SQLite, and other SQL databases.

---

## Email Operations

Send and manage emails.

**Triggers:** send email, email, mail, compose email, email client

Send emails with attachments and HTML formatting. Manage email accounts and process incoming messages.

---

## Notification System

Send notifications and alerts.

**Triggers:** send notification, notify, alert, push notification, notification

Send notifications through various channels including system notifications, webhooks, and messaging platforms.

---

## Task Scheduling

Schedule and automate recurring tasks.

**Triggers:** schedule task, cron, scheduled job, automation, recurring task, timer

Create and manage scheduled tasks with cron-like scheduling. Automate recurring operations and background jobs.

---

## Project Management

Manage projects, files, and workspace organization.

**Triggers:** project management, workspace, organize project, project structure

Organize and manage project files, dependencies, and configurations. Maintain project structure and conventions.

---

## MCP Integration

Connect to Model Context Protocol servers.

**Triggers:** mcp, model context protocol, external tools, mcp server

Integrate with external tools and services through the Model Context Protocol. Extends agent capabilities with custom tools.

---

## Backup & Restore

Create and restore backups of agent state and data.

**Triggers:** backup, restore, save state, snapshot, backup data

Create snapshots of agent memory, chat history, and workspace. Restore from previous states for disaster recovery.

---

## SSH & Remote Execution

Execute commands on remote servers via SSH.

**Triggers:** ssh, remote execution, remote server, remote command, ssh connection

Secure shell access to remote servers. Execute commands, transfer files, and manage remote systems.

---

## Docker Management

Manage Docker containers and images.

**Triggers:** docker, container, docker compose, containerization, image

Build, run, and manage Docker containers. Work with Docker Compose for multi-container applications.

---

## Visualization

Create visualizations and charts from data.

**Triggers:** visualize, chart, graph, plot, visualization, diagram

Generate visual representations of data using matplotlib, plotly, and other visualization libraries.

---

## Natural Language Processing

Process and analyze text with NLP techniques.

**Triggers:** nlp, text analysis, sentiment analysis, named entity, text processing

Advanced text processing including sentiment analysis, entity extraction, and text classification.

---

## Image Processing

Process and analyze images.

**Triggers:** image processing, image analysis, computer vision, image manipulation

Process images with operations like resizing, filtering, and analysis. Extract information from images.

---

## Audio Processing

Process and analyze audio files.

**Triggers:** audio processing, speech recognition, transcription, audio analysis

Transcribe audio, process speech, and analyze audio signals using Whisper and other audio tools.

---

## Configuration Management

Manage application and system configuration.

**Triggers:** config, configuration, settings, preferences, environment

Read, write, and manage configuration files. Handle environment variables and application settings.

---

## Error Handling

Debug and handle errors gracefully.

**Triggers:** debug, error handling, exception, troubleshoot, fix error

Sophisticated error handling with context preservation and recovery strategies. Help debug issues and suggest fixes.

---

## Documentation Generation

Generate documentation from code and specifications.

**Triggers:** generate docs, documentation, docstring, api docs, readme

Automatically generate documentation from code, including README files, API documentation, and docstrings.

---

## Code Review

Review code for quality, style, and best practices.

**Triggers:** code review, review code, code quality, style check, linting

Analyze code for issues, suggest improvements, and enforce coding standards. Integrates with linters and static analysis tools.

---

## Refactoring

Refactor code to improve structure and maintainability.

**Triggers:** refactor, code refactoring, restructure code, improve code, clean code

Safely refactor code while preserving functionality. Suggest and implement code improvements.

---

## Deployment

Deploy applications to various environments.

**Triggers:** deploy, deployment, release, publish, ship code

Handle application deployment to staging, production, and other environments. Manage release processes.

---

## Monitoring & Observability

Monitor system health and performance.

**Triggers:** monitor, observability, metrics, logging, tracing

Set up monitoring, collect metrics, and analyze system behavior. Integrate with observability platforms.

---

## Secret Management

Securely manage secrets and credentials.

**Triggers:** secrets, credentials, api keys, passwords, secure storage

Encrypt, store, and retrieve secrets securely. Manage API keys, tokens, and sensitive configuration.

---

## A2A Communication

Agent-to-agent communication and collaboration.

**Triggers:** a2a, agent communication, agent collaboration, agent network

Enable agents to communicate and collaborate across different instances and environments.

---

## Behaviour Adjustment

Dynamically adjust agent behaviour and response style.

**Triggers:** adjust behaviour, change style, modify approach, behaviour setting

Adapt agent personality, response style, and approach based on context and user preferences.

---

## RFC Processing

Process and generate RFC-style documents and exchanges.

**Triggers:** rfc, request for comments, document exchange, structured communication

Handle structured communication using RFC-style formats for proposals and technical discussions.

---

## Localization

Support multiple languages and locales.

**Triggers:** localization, translation, i18n, language support, locale

Handle internationalization and localization for multi-language support.

---

## Rate Limiting

Manage API rate limits and throttling.

**Triggers:** rate limit, throttling, api limits, quota management

Track and manage rate limits for external APIs and services to avoid quota exhaustion.

---

## Vector Database

Manage vector embeddings and semantic search.

**Triggers:** vector database, embeddings, semantic search, similarity search, faiss

Store and query vector embeddings for semantic similarity search and retrieval.

---

## SurrealDB Integration

Work with SurrealDB for advanced data operations.

**Triggers:** surrealdb, surreal, graph db, multi-model database

Leverage SurrealDB for knowledge storage, graph operations, and flexible data modeling.

---

**Note**: These skills are loaded lazily on-demand when their triggers match the current task context. Additional project-specific skills can be added to `.agent-zero/skills/` directory.

For detailed skill implementation and usage, see the corresponding tools and extensions in the Agent Zero codebase.
