---
tags: [component, prompts, configuration]
---

# Prompts System

Prompts define the agent's persona and instructions.

## Structure

- `prompts/`: Root directory.
- `prompts/default/`: Default system prompts.
    - `agent.system.main.md`: The master prompt.
    - `agent.system.tools.md`: Tool definitions.

## Key Prompts

- [[Agent Zero System Prompt]] (`prompts/default/agent.system.md` - inferred name)
- [[Solving Strategy]] (`prompts/agent.system.main.solving.md`)

## Relations

- [[Agent Core]] parses these files to send to the LLM.

