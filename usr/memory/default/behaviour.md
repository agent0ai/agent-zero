## Behavioral Rules

* Favor linux commands for simple tasks where possible instead of python

## Model Routing

* Default model is claude-sonnet-4-6 for general tasks, simple questions, and tool calls
* Use claude-opus-4-6 for tasks requiring deeper reasoning, complex problem solving, advanced coding architecture, multi-step planning, or high-stakes decisions
* Use **Codex CLI (gpt-5.3-codex)** for writing new code files, scaffolding, boilerplate generation >50 lines, test generation, and build/test verification. Access via: `codex exec --skip-git-repo-check -s read-only --dangerously-bypass-approvals-and-sandbox -o /tmp/output.md '<prompt>'`
* Use **Gemini 2.5 Pro** for reading/understanding large codebases, code reviews, architecture analysis, large document analysis (1M token context), PRD analysis, and brainstorming. Access via `gemini.ask-gemini` MCP tool with `model: 'gemini-2.5-pro'`
* **Quick routing rule:** Code reading → Gemini · Code writing (>50 lines) → Codex · Quality-critical/Architecture/Security → Opus · General/Code <50 lines → Sonnet · Utility/Parsing/Memory → Haiku
* Route complex tasks by delegating to a subordinate with claude-opus-4-6 via the call_subordinate tool, or noting the model preference in the task description

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
* Use native tools instead: `memory_save` for project context, `plan.md` for plans, `call_sub` for subordinates, chat history for session state
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

## Parallel Model Execution

* For independent subtasks that can run simultaneously, use parallel terminal sessions: start long-running processes (Codex, heavy scripts) in session 1 while using session 0 or MCP tools concurrently — do not wait sequentially if tasks are independent
* Pattern for parallel Gemini + Codex: (1) start Codex in session 1 via terminal background or separate session, (2) call gemini.ask-gemini MCP immediately after without waiting, (3) then collect session 1 output with runtime:output
* When to parallelize: multiple files need analysis + generation simultaneously, or when one task does not depend on the output of another
* When NOT to parallelize: when Codex output is needed as input for Gemini review, or when tasks share the same files (write conflicts)

## Git Workflow & PR Convention

* Always create a feature branch — never commit directly to main
* Branch naming: `feature/az-<name>` for features, `fix/az-<name>` for bugfixes
* Always write tests for new code (pytest, use existing test patterns)
* Run tests locally before pushing: check test_command in `.ai-review.yml` if present
* Open PR with a clear summary: What changed, Why, How to test
* PRs from `feature/az-*` and `fix/az-*` branches trigger automatic AI code review
* If AI review finds CRITICAL/BUG issues, fix them before requesting human merge