# Agent Skills

Agent Skills provide specialized capabilities to Agent Zero through progressive disclosure.

## Structure

- `custom/` - User-created skills
- `builtin/` - Framework-provided skills
- `shared/` - Community/imported skills

## Skill Format

Each skill is a directory containing:
- `SKILL.md` - Main skill definition with YAML frontmatter
- `reference.md` - Additional context files (optional)
- `scripts/` - Executable scripts (optional)

## Creating a Skill

1. Create directory in `skills/custom/my_skill/`
2. Create `SKILL.md` with YAML frontmatter:

```yaml
---
name: "my_skill"
description: "Brief description for metadata"
version: "1.0.0"
tags: ["tag1", "tag2"]
---

# Skill Content

Detailed instructions and procedures...
```

3. Add reference files and scripts as needed
4. Skill automatically loads at next agent startup
