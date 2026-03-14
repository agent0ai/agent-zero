---
name: example-skill
version: "1.0.0"
author: Agent Jumbo Team
tier: 1
trust_level: builtin
description: A demonstration skill showing the SKILL.md format for Tier 1 markdown skills.
categories:
  - examples
  - documentation
dependencies: []
capabilities:
  - text-generation
enabled: true
---

# Example Skill

This is a **Tier 1** markdown skill. Its content is injected into the agent's
system prompt at runtime, giving the agent new knowledge or behavioural
instructions without any Python code.

## Usage

When this skill is enabled, the agent gains the following ability:

- Respond to questions about the SKILL.md format
- Explain the difference between Tier 1 and Tier 2 skills
- Demonstrate frontmatter fields and their meanings

## SKILL.md Format Reference

| Field         | Required | Description                                      |
|---------------|----------|--------------------------------------------------|
| name          | Yes      | Unique skill identifier                          |
| version       | Yes      | Semantic version string                          |
| author        | Yes      | Skill author or organisation                     |
| tier          | No       | 1 (markdown) or 2 (Python module), default 1     |
| trust_level   | No       | builtin / verified / community / local           |
| categories    | No       | List of category tags                            |
| dependencies  | No       | List of required skill names                     |
| capabilities  | No       | List of capability declarations                  |
| enabled       | No       | Whether the skill is active, default true         |
| description   | No       | Short human-readable summary                     |
