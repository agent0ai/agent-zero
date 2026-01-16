# Agent Zero Skills Directory

This directory contains project-local Agent Skills following the Anthropic Agent Skills Standard.

## Overview

Agent Skills are modular, reusable capabilities that extend Agent Zero's functionality. Skills are discovered automatically and loaded on-demand when needed.

## Directory Structure

```
.agent-zero/skills/
├── README.md (this file)
├── skill-name-1/
│   ├── SKILL.md (required)
│   ├── run.py (optional executable)
│   └── ... (additional resources)
└── skill-name-2/
    ├── SKILL.md
    └── ...
```

## Skill Discovery

Agent Zero discovers skills from multiple locations in priority order:

1. **Project-local** (highest priority):
   - `.agent-zero/skills/`
   - `.opencode/skills/`
   - `.claude/skills/`

2. **Global configuration**:
   - `~/.config/agent-zero/skills/`
   - `~/.config/opencode/skills/`
   - `~/.config/claude/skills/`

3. **Manifest-based**:
   - `AGENTS.md` in project root

## Creating a Skill

### Option 1: Complete SKILL.md with Frontmatter

Create a new directory under `.agent-zero/skills/` with a `SKILL.md` file:

```markdown
---
name: my-skill
description: Brief description of what this skill does
triggers: keyword1, keyword2, keyword3
version: 1.0.0
author: Your Name
license: MIT
---

# My Skill

Detailed instructions for the agent on how to use this skill.

## Usage

Provide clear, actionable instructions that the agent can follow.

## Examples

Include examples of when and how to use this skill.

## Dependencies

List any required tools, APIs, or other skills.
```

### Option 2: Simple SKILL.md

Create a minimal `SKILL.md` without frontmatter:

```markdown
## My Skill

Brief description of what this skill does.

**Triggers:** keyword1, keyword2, keyword3

Detailed instructions...
```

## Skill Format Requirements

### Name Validation

- Must be lowercase alphanumeric with hyphens only
- Pattern: `^[a-z0-9]+(-[a-z0-9]+)*$`
- Length: 1-64 characters
- Examples: `github-integration`, `security-scanner`, `data-analysis`

### Description

- Required field
- Maximum 1024 characters
- Should clearly explain the skill's purpose and capabilities

### Triggers

- Optional but recommended
- Keywords or phrases that activate the skill
- Agent uses these to determine when a skill is relevant
- Can be comma-separated in frontmatter or listed after `**Triggers:**`

## Adding Executable Scripts

Skills can include executable Python scripts for complex operations:

1. Create a `run.py`, `execute.py`, or `main.py` in the skill directory
2. Implement an `execute()` or `main()` async function:

```python
async def execute(agent, args):
    """
    Execute the skill

    Args:
        agent: Agent instance
        args: Dictionary of arguments

    Returns:
        Execution result (string or dict)
    """
    # Your skill logic here
    return "Skill executed successfully"
```

## Installing Skills from Marketplaces

Agent Zero is compatible with existing Agent Skills marketplaces:

### From skilz

```bash
skilz install github-integration
# Skill is automatically discovered by Agent Zero
```

### From n-skills

```bash
n-skills add security-scanner
# Skill is automatically available
```

### From OpenSkills

```bash
opencode install data-analysis
# Compatible with Agent Zero
```

### Manual Installation

Copy a skill directory to `.agent-zero/skills/` or use the API:

```bash
curl -X POST http://localhost:50001/api/skills/install \
  -H "Content-Type: application/json" \
  -d '{"path": "/path/to/skill", "target": "project"}'
```

## Skill APIs

Agent Zero provides REST APIs for skill management:

### List All Skills

```bash
curl http://localhost:50001/api/skills/list
```

### Search Skills

```bash
curl -X POST http://localhost:50001/api/skills/search \
  -H "Content-Type: application/json" \
  -d '{"query": "github"}'
```

### Get Skill Details

```bash
curl http://localhost:50001/api/skills/get?name=github-integration
```

### Force Discovery

```bash
curl -X POST http://localhost:50001/api/skills/discover
```

### Get Statistics

```bash
curl http://localhost:50001/api/skills/stats
```

## Skill Activation

Skills are activated in several ways:

1. **Automatic (Trigger-based)**: Agent detects relevant triggers in conversation
2. **Explicit Request**: User asks for a specific skill by name
3. **Context-aware**: Agent loads skills based on current task context
4. **Tool Invocation**: Skills can be invoked as tools in the agent's workflow

## Best Practices

### Skill Design

- **Single Responsibility**: Each skill should do one thing well
- **Clear Instructions**: Write instructions as if for a human assistant
- **Progressive Detail**: Start with overview, then provide specifics
- **Actionable**: Focus on what the agent should *do*, not just information
- **Testable**: Include examples and test cases

### Naming

- Use descriptive, hyphenated names: `github-pr-review`, not `gpr`
- Avoid overly generic names: `security-scanner`, not `scanner`
- Consistent with ecosystem conventions

### Documentation

- Always include a description
- List all triggers that should activate the skill
- Document any required configuration or API keys
- Provide usage examples

### Dependencies

- List other skills this skill depends on
- Specify required tools, APIs, or services
- Include installation instructions for external dependencies

## Skill Composition

Skills can reference and build upon other skills:

```markdown
---
name: advanced-github
description: Advanced GitHub workflow automation
dependencies:
  - github-integration
  - security-scanner
---

# Advanced GitHub Workflow

This skill combines GitHub integration and security scanning...
```

## Global vs. Project Skills

### Global Skills (`~/.config/agent-zero/skills/`)

- Available to all projects
- Useful for general-purpose capabilities
- Examples: git-workflow, code-review, documentation

### Project Skills (`.agent-zero/skills/`)

- Specific to the current project
- Project-specific workflows and conventions
- Override global skills with same name

## Marketplace Integration

Agent Zero integrates with existing Agent Skills marketplaces:

- **SkillsMP**: https://skillsmp.com
- **Skillstore**: Security-audited skills
- **GitHub**: Direct repository installation
- **OpenSkills**: Universal skill loader

Skills installed via these marketplaces are automatically discovered and available.

## Troubleshooting

### Skill Not Found

1. Check skill name matches directory name
2. Verify `SKILL.md` exists in skill directory
3. Ensure name follows validation rules (lowercase, hyphens only)
4. Force discovery: `POST /api/skills/discover`

### Skill Not Activating

1. Verify triggers are relevant to your use case
2. Check skill description is clear and specific
3. Try explicit request: "Use the [skill-name] skill"
4. Review agent logs for skill loading errors

### Installation Issues

1. Verify path is correct
2. Check file permissions
3. Ensure SKILL.md is valid (parse errors logged)
4. Try manual copy to `.agent-zero/skills/`

## Examples

See the project's `AGENTS.md` for example skill definitions used in this project.

## References

- **Anthropic Agent Skills Spec**: https://agentskills.io/specification
- **OpenCode Skills**: https://opencode.ai/docs/skills/
- **Awesome Agent Skills**: https://github.com/skillmatic-ai/awesome-agent-skills

## Contributing

To contribute skills to Agent Zero:

1. Create your skill following this format
2. Test it in your local `.agent-zero/skills/` directory
3. Share via GitHub or submit to skill marketplaces
4. Skills are portable across all Agent Skills-compatible platforms

---

**Note**: This skill system is fully compatible with the Anthropic Agent Skills Standard and works with existing skill marketplaces. You don't need to create a new marketplace - just use existing ones!
