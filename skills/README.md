# Agent Jumbo Skill Format

This document describes how to create, test, and publish skills for Agent Jumbo.

## Directory Structure

A skill lives in its own directory under `skills/`:

```text
skills/
  my-skill/
    SKILL.md           # Required: manifest + documentation
    main.py            # Optional: Tier 2 entry point
    requirements.txt   # Optional: Python dependencies
    tests/             # Optional: test suite
    examples/          # Optional: usage examples
```

## SKILL.md Format

Every skill must contain a `SKILL.md` file with YAML frontmatter followed by a Markdown body.

### Frontmatter Fields

```yaml
---
name: my-skill                    # Required. Unique identifier (lowercase, hyphens).
version: 1.0.0                   # Required. Semver string.
author: your-name                 # Required. Author or organization name.
description: >                    # Recommended. What the skill does and when to use it.
  Short description of what this skill does.

tier: 1                           # Optional (default: 1).
                                  #   1 = Markdown-only (instructions in SKILL.md body)
                                  #   2 = Python module (code in *.py files)

trust_level: community            # Optional (default: community).
                                  #   builtin  - Ships with Agent Jumbo core
                                  #   verified - Reviewed and signed by maintainers
                                  #   community - Published on JumboHub, not yet verified
                                  #   local    - Installed from a local path

categories:                       # Optional. Categorization tags.
  - automation
  - productivity

dependencies:                     # Optional. Other skill names this skill requires.
  - some-other-skill

capabilities:                     # Optional. Declared system capabilities used.
  - filesystem                    #   filesystem - reads/writes files
  - network                       #   network    - makes HTTP requests
  - process                       #   process    - spawns subprocesses

enabled: true                     # Optional (default: true). Whether the skill is active.
---
```

### Markdown Body

The body after the closing `---` is free-form Markdown. It should describe:

1. **What the skill does** -- purpose and use cases.
2. **Core workflow** -- step-by-step instructions the agent follows.
3. **Implementation guardrails** -- constraints, error handling, and edge cases.
4. **Extension notes** -- how to add new features or data sources.

## Tier 1 vs Tier 2 Skills

### Tier 1: Markdown Skills

Tier 1 skills are pure instructions. The `SKILL.md` body tells Agent Jumbo *how* to
accomplish a task using its existing tools (memory, knowledge, instruments, MCP servers).

- No Python code required.
- Activated by matching the skill description against the user's request.
- Safe by default -- no code beyond what Agent Jumbo already supports.

**Best for:** prompt templates, workflows, brand guidelines, domain knowledge.

### Tier 2: Python Skills

Tier 2 skills include Python code (`main.py` or other `.py` files) that
Agent Jumbo can import and run.

- Must declare all system capabilities used (filesystem, network, process).
- Subject to the security scanner before installation.
- Can define custom instruments, tools, or integrations.

**Best for:** API integrations, data processing, custom tool implementations.

## Security Guidelines

### For Skill Authors

- Declare all capabilities your skill uses in the frontmatter.
- Never call `eval()`, `exec()`, `compile()`, or `__import__()`.
- Avoid importing `os`, `subprocess`, `shutil`, `ctypes`, or `socket` unless
  the corresponding capability is declared.
- Do not include secrets, API keys, or credentials in your skill files.
- Provide tests so users can verify behavior.

### For Skill Users

- Always run `python -m python.cli.skill_cli scan <path>` before installing a
  community skill.
- Review the scan results. HIGH and CRITICAL findings mean the skill uses
  dangerous operations.
- Prefer `verified` and `builtin` trust levels for production use.
- Check the `capabilities` field -- a "productivity" skill should not need
  `process` or `filesystem` capabilities.

## Creating a Skill

1. Create a directory under `skills/`:

   ```bash
   mkdir skills/my-skill
   ```

2. Write `SKILL.md` with frontmatter and instructions:

   ```markdown
   ---
   name: my-skill
   version: 0.1.0
   author: your-name
   description: Does something useful when asked to do X.
   tier: 1
   categories:
     - utility
   ---

   # My Skill

   ## Core workflow

   1. Gather requirements from the user.
   2. Apply the following template...
   3. Return the formatted result.
   ```

3. For Tier 2, add Python files:

   ```python
   # skills/my-skill/main.py
   def run(context):
       """Entry point called by the skill loader."""
       return {"status": "ok"}
   ```

4. Add tests (optional but recommended):

   ```text
   skills/my-skill/tests/test_main.py
   ```

## Testing a Skill

Run the security scanner:

```bash
python -m python.cli.skill_cli scan skills/my-skill
```

List installed skills:

```bash
python -m python.cli.skill_cli list
```

View skill details:

```bash
python -m python.cli.skill_cli info my-skill
```

## Packaging and Publishing

### Package a skill

```bash
python -m python.cli.skill_cli package skills/my-skill
```

This creates `my-skill.tar.gz` with a SHA256 hash for integrity verification.

### Publish to JumboHub

```bash
export JUMBOHUB_TOKEN=ghp_your_token
python -m python.cli.skill_cli publish skills/my-skill
```

Publishing creates a GitHub release on the JumboHub repository with the packaged
archive and its SHA256 hash.

### Install from JumboHub

```bash
python -m python.cli.skill_cli install my-skill
```

### Install from a local path

```bash
python -m python.cli.skill_cli install /path/to/my-skill
```

### Install from a package file

```bash
python -m python.cli.skill_cli install my-skill.tar.gz
```

## Example Frontmatter

```yaml
---
name: stripe-revenue-analyzer
version: 1.2.0
author: agent-jumbo-team
description: >
  Analyze Stripe revenue data, generate reports, and identify trends.
  Use when asked about revenue, MRR, churn, or Stripe analytics.
tier: 2
trust_level: verified
categories:
  - analytics
  - finance
dependencies:
  - data-visualization
capabilities:
  - network
enabled: true
---
```
