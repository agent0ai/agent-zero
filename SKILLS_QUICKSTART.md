# Agent Skills Quick Start Guide

Get started with Agent Skills in Agent Zero in 5 minutes.

## What Are Agent Skills?

Agent Skills are modular capabilities defined in SKILL.md files that:
- Load on-demand when needed
- Follow the Anthropic Agent Skills Standard
- Work with existing marketplaces (skilz, n-skills, OpenSkills)
- Extend agent capabilities without code changes

## Quick Start

### 1. Verify Installation

```bash
python verify_skills_integration.py
```

Expected: ✓ All files present, parser working, 46 skills discovered

### 2. List Available Skills

```bash
curl http://localhost:50001/api/skills/list | jq '.skills[] | {name, description}'
```

### 3. Create Your First Skill

```bash
# Create directory
mkdir -p .agent-zero/skills/hello-world

# Create SKILL.md
cat > .agent-zero/skills/hello-world/SKILL.md << 'EOF'
---
name: hello-world
description: A simple hello world skill
triggers: hello, greet, greeting
---

# Hello World Skill

When activated, greet the user warmly and explain what skills are.

## Instructions

1. Say "Hello! I've activated the Hello World skill."
2. Explain that skills are modular capabilities
3. Mention this skill was triggered by keywords: hello, greet, greeting
EOF
```

### 4. Discover and Test

```bash
# Force discovery
curl -X POST http://localhost:50001/api/skills/discover

# Verify skill was found
curl http://localhost:50001/api/skills/get?name=hello-world
```

### 5. Use in Chat

Start Agent Zero and say: "Hello" or "Greet me"

The agent will automatically load and use the hello-world skill!

## Install From Marketplace

### skilz

```bash
skilz install github-integration
# Automatically available in Agent Zero
```

### n-skills

```bash
n-skills add security-scanner
# Ready to use immediately
```

### Manual Install

```bash
# Copy skill to project
cp -r /path/to/skill .agent-zero/skills/

# Or via API
curl -X POST http://localhost:50001/api/skills/install \
  -H "Content-Type: application/json" \
  -d '{"path": "/path/to/skill", "target": "project"}'
```

## Skill Template

```markdown
---
name: my-skill
description: What this skill does (required, max 1024 chars)
triggers: trigger1, trigger2, trigger3
version: 1.0.0
author: Your Name
license: MIT
---

# Skill Name

Detailed description and purpose.

## What This Skill Does

Clear explanation of capabilities.

## Instructions for Agent

Step-by-step instructions:
1. First do this
2. Then do that
3. Finally accomplish the goal

## Examples

**Example 1:**
User: "trigger phrase"
Agent response: "..."

**Example 2:**
User: "another trigger"
Agent response: "..."

## Requirements

- List any required tools
- API keys needed
- Dependencies on other skills
```

## API Cheat Sheet

```bash
# List all skills
GET /api/skills/list

# Search skills
POST /api/skills/search
{"query": "github"}

# Get skill details
GET /api/skills/get?name=skill-name

# Force discovery
POST /api/skills/discover

# Get statistics
GET /api/skills/stats

# Get skills by trigger
POST /api/skills/by-trigger
{"trigger": "github"}

# Install skill
POST /api/skills/install
{"path": "/path/to/skill", "target": "project"}
```

## Python API

```python
from python.helpers.agent_skills import get_integration

# Get integration
integration = get_integration()

# Discover skills
integration.discover_and_register()

# List skills
skills = integration.get_available_skills_for_agent()
print(f"Found {len(skills)} skills")

# Search
results = integration.search_skills("code")

# Get details
details = integration.get_skill_details("github-integration")

# Stats
stats = integration.get_stats()
```

## Skill Locations

Skills are discovered from (in priority order):

1. **Project**: `.agent-zero/skills/`
2. **Project**: `.opencode/skills/`
3. **Project**: `.claude/skills/`
4. **Global**: `~/.config/agent-zero/skills/`
5. **Global**: `~/.config/opencode/skills/`
6. **Manifest**: `AGENTS.md` in project root

## Built-in Skills

Agent Zero includes 45+ built-in skills in `AGENTS.md`:

- Code Execution
- Memory Management
- Knowledge Base Query
- Web Browsing
- File Management
- Git Integration
- Data Analysis
- Security Scanning
- And many more!

View all: `curl http://localhost:50001/api/skills/list`

## Advanced: Executable Skills

Add a `run.py` file to make skills executable:

```python
# .agent-zero/skills/my-skill/run.py

async def execute(agent, args):
    """
    Execute the skill

    Args:
        agent: Agent instance with full capabilities
        args: Dictionary of arguments from tool invocation

    Returns:
        Result string or dictionary
    """
    # Access agent capabilities
    result = await agent.call_utility_llm("Analyze this data...")

    # Use tools
    await agent.read_file("data.txt")

    # Return result
    return {
        "status": "success",
        "data": result
    }
```

## Troubleshooting

### Skill not found?

```bash
# Check it exists
ls .agent-zero/skills/my-skill/SKILL.md

# Force discovery
curl -X POST http://localhost:50001/api/skills/discover

# Check name is valid (lowercase, hyphens only)
echo "my-skill" | grep -E '^[a-z0-9]+(-[a-z0-9]+)*$'
```

### Skill not activating?

1. Check triggers are relevant
2. Try explicit: "Use the my-skill skill"
3. Verify description is clear
4. Check agent logs

### Parse errors?

```bash
# Validate YAML frontmatter
python -c "
import yaml
with open('.agent-zero/skills/my-skill/SKILL.md') as f:
    content = f.read()
    if content.startswith('---'):
        parts = content.split('---', 2)
        yaml.safe_load(parts[1])
"
```

## Next Steps

- Read full docs: `docs/AGENT_SKILLS_INTEGRATION.md`
- Browse example: `.agent-zero/skills/example-skill/SKILL.md`
- View built-in skills: `AGENTS.md`
- Run tests: `pytest tests/test_agent_skills.py`
- Create your own skills!

## Resources

- **Specification**: https://agentskills.io/specification
- **Examples**: https://github.com/anthropics/skills
- **Awesome Skills**: https://github.com/skillmatic-ai/awesome-agent-skills
- **OpenCode Docs**: https://opencode.ai/docs/skills/

## Support

- Check `.agent-zero/skills/README.md` for detailed information
- Review `docs/AGENT_SKILLS_INTEGRATION.md` for technical details
- Run `python verify_skills_integration.py` to check system health

---

**Happy skill building!** 🚀

Skills make agents more capable, one module at a time.
