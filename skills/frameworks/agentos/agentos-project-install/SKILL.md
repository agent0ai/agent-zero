---
name: "agentos-project-install"
description: "Initialize a project with AgentOS standard structure and configuration."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["agentos", "initialization", "setup"]
trigger_patterns:
  - "install agentos"
  - "setup project"
  - "initialize agentos"
---

# AgentOS: Project Install

Initialize a project with AgentOS standard structure and configuration files.

## When to Use

- Starting a new project with AgentOS
- Converting existing project to AgentOS standards
- Setting up development environment

## Standard Structure

```
project/
├── .agentos/
│   ├── config.yaml        # Project configuration
│   ├── standards.yaml     # Coding standards
│   └── hooks/             # Git hooks
├── docs/
│   ├── README.md
│   └── CONTRIBUTING.md
├── src/
├── tests/
├── .gitignore
├── .editorconfig
└── Makefile
```

## Installation Process

1. **Create Directory Structure**
   - Create `.agentos/` configuration directory
   - Set up standard folders
   - Add configuration files

2. **Initialize Configuration**
   ```yaml
   # .agentos/config.yaml
   project:
     name: [Project Name]
     type: [web/cli/library]
     language: [Primary language]

   standards:
     linting: true
     formatting: true
     testing: required

   quality:
     coverage_minimum: 80
     review_required: true
   ```

3. **Set Up Git Hooks**
   - Pre-commit: linting, formatting
   - Pre-push: tests

4. **Create Documentation**
   - README template
   - Contributing guidelines

## Output

```markdown
## AgentOS Installed: [Project Name]

**Config**: `.agentos/config.yaml`
**Standards**: Configured
**Hooks**: Installed

Project ready for development.

Apply standards with `agentos-standards`.
```
