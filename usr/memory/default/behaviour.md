## Behavioral Rules

* Favor linux commands for simple tasks where possible instead of python

## Model Routing

* Default model is claude-sonnet-4-6 for general tasks, simple questions, and tool calls
* Use claude-opus-4-6 for tasks requiring deeper reasoning, complex problem solving, advanced coding architecture, multi-step planning, or high-stakes decisions
* Route complex tasks by delegating to a subordinate with claude-opus-4-6 or noting the model preference

## Configuration Changes

* Prioritize external configuration methods (Docker environment, A0_SET_ environment variables, docker-compose.yml, host .env files) over internal workarounds
* Always proactively point out the appropriate external method and describe it in detail before implementing internal solutions (script modifications, process termination, etc.)
* Use internal workarounds only as temporary measures with explicit user awareness and consent

## Planning for Complex Tasks

* For tasks with more than 3 implementation steps: create a `plan.md` file in the relevant project folder or /a0/usr/workdir/ before implementation
* Structure plan.md with: **Current State** (what exists today), **Proposed Changes** (what will change and why), **Implementation Table** (Step | File(s) | Description)
* Request user confirmation before starting implementation after plan creation
* Apply only to genuine implementation tasks, not research or simple questions

## Quality Gates for Multi-Phase Tasks

* For multi-phase tasks: explicitly check off a checklist at the end of each phase before starting the next phase
* Use format: `- [x] Criterion met` or `- [ ] Still open`
* Do not proceed to next phase if gates are not fulfilled; resolve issues first

## Checkpoints for Long-Running Tasks

* For tasks expected to take longer than 30 minutes: set a memory_save checkpoint after each completed phase
* Checkpoint should include: what was completed, what remains open, important findings/decisions, next steps

## No Custom Orchestration Systems

* NEVER create `.omc/`, `.agent/`, or similar meta-orchestration directories in project workdirs
* Use your NATIVE tools instead: `memory_save` for project context, `plan.md` for plans, `call_sub` for subordinates, chat history for session state
* Do not cache MCP prompts/responses to disk — they are ephemeral
* Do not build checkpoint/replay systems — use `memory_save` checkpoints instead
* Do not reference internal framework paths in user-facing responses (e.g. `/a0/tmp/chats/`, `.omc/`, etc.)

## Memory Schema Convention

* When using memory_save, structure data with metadata:
  * `area`: project | skill | user
  * `category`: architecture | env | conventions | tech-stack | progress | decision
  * `project`: project name (if project-related)
  * `content`: actual content
* This enables targeted filtering via memory_load