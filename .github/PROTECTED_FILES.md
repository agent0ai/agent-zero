# Protected Files - Agent Safety Documentation

## Overview

This document explains the protections in place to prevent Copilot agents from modifying critical workflow and configuration files.

## Protected Directories

The following directories contain files that define agent behavior and MUST NOT be modified by agents:

1. **`.github/prompts/`** - Workflow prompt templates
2. **`.github/agents/`** - Agent definition files
3. **`.github/instructions/`** - Copilot instruction files

## Protection Mechanisms

### 1. Explicit Instructions in copilot-instructions.md

The main instruction file contains a **CRITICAL** section at the top:

```markdown
**CRITICAL: PROTECTED FILES - DO NOT MODIFY**
- **NEVER modify, edit, update, or replace files in `.github/prompts/`**
- **NEVER modify, edit, update, or replace files in `.github/agents/`**
- **NEVER modify, edit, update, or replace files in `.github/instructions/`**
- These files define agent behavior and workflows - they are READ-ONLY
- If you believe changes are needed to these files, STOP and inform the user
- Violation of this rule means the agent is malfunctioning
```

This instruction appears FIRST, before any other instructions, giving it maximum priority.

### 2. Per-Agent Protections

Each agent file (`.github/agents/*.md`) includes the same protection warning at the top of their instructions, immediately after their title:

- `memory-deep-think.agent.md`
- `architect.agent.md`
- `code.agent.md`
- `debug.agent.md`
- `ask.agent.md`

### 3. Self-Documenting Prompt Files

Each prompt template file (`.github/prompts/*.md`) includes a warning header:

```markdown
**⚠️ CRITICAL: THIS FILE IS READ-ONLY ⚠️**
**DO NOT MODIFY THIS PROMPT FILE. It is a template for agent workflows.**
**All work, plans, and context must be saved to AI-Memory/, NOT here.**
```

This serves as both a protection and a reminder that outputs should go to `AI-Memory/`, not back into the prompt files.

### 4. .copilotignore File

A `.github/.copilotignore` file explicitly lists the protected directories:

```
# Agent definition files
agents/*.md

# Prompt template files
prompts/*.md

# Instruction files
instructions/*.md
```

## What To Do If a File Is Modified

If you notice that an agent has modified a file in these protected directories:

1. **Immediately stop the agent** - The agent is malfunctioning
2. **Restore the file** from git history: `git restore .github/prompts/filename.md`
3. **Review the changes** to understand what the agent was trying to do
4. **Report the issue** - This indicates a failure in the protection mechanisms
5. **Consider if the legitimate intent** requires updating the instructions

## Legitimate Modifications

Only humans should modify these files, and only when:

- Adding new workflow patterns
- Updating agent capabilities
- Fixing bugs in prompt logic
- Improving instruction clarity
- Adding new protection mechanisms

## File Purposes

### Prompt Files (`.github/prompts/`)
- `Think.prompt.md` - Deep research and analysis workflow
- `Plan.prompt.md` - Task breakdown and planning workflow
- `Execute.prompt.md` - Implementation and execution workflow
- `Checkpoint.prompt.md` - Memory bank checkpoint workflow
- `Startup.prompt.md` - Session initialization workflow
- `GH.prompt.md` - GitHub Actions monitoring workflow
- `Sync.prompt.md` - Memory-codebase synchronization workflow

### Agent Files (`.github/agents/`)
- `memory-deep-think.agent.md` - Memory management and deep thinking
- `architect.agent.md` - System architecture and design
- `code.agent.md` - Code implementation
- `debug.agent.md` - Debugging and troubleshooting
- `ask.agent.md` - Questions and documentation

### Instruction Files (`.github/instructions/`)
- `copilot-instructions.md` - Main Copilot configuration

## Output Destinations

Agents should output their work to:

- **`AI-Memory/`** - For context, decisions, progress, patterns
- **`app/`, `components/`, `lib/`** - For code implementation
- **`docs/`** - For project documentation
- **Root config files** - For build/deployment configuration

Agents should **NEVER** write output back to:
- `.github/prompts/`
- `.github/agents/`
- `.github/instructions/`

## Monitoring

To check if protected files have been modified:

```bash
# Check git status for any changes in .github
git status .github/

# View changes to protected directories
git diff .github/prompts/
git diff .github/agents/
git diff .github/instructions/

# Check recent commits affecting these files
git log --oneline -- .github/prompts/ .github/agents/ .github/instructions/
```

## Version History

- 2025-11-19: Initial protection mechanisms implemented
  - Added CRITICAL warning to copilot-instructions.md
  - Added protection warnings to all agent files
  - Added read-only warnings to all prompt files
  - Created .copilotignore file
  - Created this documentation
- 2025-12-01: Updated for AI-Memory folder structure
  - Changed memory-bank references to AI-Memory
  - Updated file list (consolidated to 5 files)

---

**Remember: These protections exist because agents must follow workflows, not redefine them.**
