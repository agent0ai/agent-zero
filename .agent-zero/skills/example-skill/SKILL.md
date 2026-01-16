---
name: example-skill
description: Example skill demonstrating the Agent Skills Standard format
triggers: example, demo, test skill
version: 1.0.0
author: Agent Zero Team
license: MIT
---

# Example Skill

This is an example skill that demonstrates the Agent Skills Standard format and integration with Agent Zero.

## Purpose

This skill serves as a template and reference implementation for creating new skills. It shows:

- Proper SKILL.md format with YAML frontmatter
- Clear instructions for the agent
- Trigger keywords for automatic activation
- Integration with Agent Zero's tool system

## Usage

This skill is activated when the agent encounters any of these triggers:
- "example"
- "demo"
- "test skill"

When activated, this skill provides guidance on how skills work in Agent Zero.

## Instructions for the Agent

When this skill is activated:

1. Acknowledge that you've loaded the example skill
2. Explain what Agent Skills are and how they work
3. Provide examples of how to create new skills
4. Reference the `.agent-zero/skills/README.md` for detailed documentation

## Features Demonstrated

- **YAML Frontmatter**: Metadata at the top of the file
- **Markdown Content**: Clear, structured instructions
- **Trigger Keywords**: Automatic activation based on context
- **Versioning**: Track skill versions for updates
- **Licensing**: Clear license information

## Example Response

When activated, you might respond:

> I've loaded the Example Skill! This demonstrates how Agent Skills work in Agent Zero.
>
> Agent Skills are modular capabilities defined in SKILL.md files. They:
> - Are discovered automatically from configured directories
> - Load on-demand when triggers match the context
> - Provide clear instructions for the agent to follow
> - Can include executable scripts for complex operations
>
> To create your own skill, add a directory under `.agent-zero/skills/` with a SKILL.md file following this format.

## Next Steps

- Review the Skills README: `.agent-zero/skills/README.md`
- Explore the Agent Zero Skills API: `POST /api/skills/list`
- Install skills from marketplaces: skilz, n-skills, OpenSkills
- Create custom skills for your project's specific needs

## Dependencies

None - this is a standalone example skill.

## Notes

This skill demonstrates the minimum viable format. Real skills can be much more sophisticated, including:

- Executable Python scripts (run.py, execute.py)
- Additional resource files (templates, configs, data)
- Dependencies on other skills
- Integration with external APIs and services
