# Task Breakdown and Action Plan Prompt

**⚠️ CRITICAL: THIS FILE IS READ-ONLY ⚠️**
**DO NOT MODIFY THIS PROMPT FILE. It is a template for agent workflows.**

## ⛔ PLANNING ONLY - NO CODE EDITING

**This prompt is for PLANNING and TASK BREAKDOWN only.**
- **DO NOT** create, edit, or modify any code files
- **DO NOT** create separate documentation files
- **ALL output MUST go through aiSkeleton memory tools**

| Output Type | Required Tool | Purpose |
|---|---|---|
| Implementation Plans | `aiSkeleton_savePlan` | Task breakdown, step-by-step planning |
| Plans/Tasks Status | `aiSkeleton_updateProgress` | Track plan status (done/doing/next) |
| Context | `aiSkeleton_updateContext` | Current planning focus, blockers |
| Decisions | `aiSkeleton_logDecision` | Design decisions made during planning |

**When planning is complete:** State "Planning complete. Handoff to Execute mode for implementation."

---

## Instructions

Use this prompt to break down any complex task into actionable steps, assign #todos for each, and utilize available tools for tracking and execution. Each step should be clear, specific, and saved to Memory via aiSkeleton tools.

**Important:** This prompt template is for planning only. All generated plans, tasks, and progress must be saved via aiSkeleton memory tools.

---

## 1. Define the Main Task

**Task:**  
<Describe the main objective or project here.>

---

## 2. Break Down the Task

**Major Components or Steps:**  
- <Step 1>
- <Step 2>
- <Step 3>
- ...

---

## 3. Outline Actionable Steps for Each Component

### Step 1: <Step Name>
- <Action 1>
- <Action 2>
- ...

### Step 2: <Step Name>
- <Action 1>
- <Action 2>
- ...

---

## 4. Assign #todos

For each actionable step, create a #todo:

- #todo <Action 1 of Step 1>
- #todo <Action 2 of Step 1>
- #todo <Action 1 of Step 2>
- ...

---

## 5. Utilize Tools

For each step, specify which tools or functions to use (e.g., code generation, unit testing, project management):

- <Step/Action>: <Tool/Function>
- ...

---

## 6. Save to Memory Management

**Use `aiSkeleton_*` tools to save all task data:**

- Save the complete plan using `aiSkeleton_updateProjectBrief`
- Store task breakdown in the project context
- Log each #todo to the progress tracking system using `aiSkeleton_updateProgress`
- Update active context with current task focus using `aiSkeleton_updateContext`
- Document key decisions made during planning using `aiSkeleton_logDecision`

**Memory Management Actions:**
- Use `aiSkeleton_updateProgress` to track task status
- Use `aiSkeleton_logDecision` for important choices
- Use `aiSkeleton_updateContext` to set current focus
- Use `aiSkeleton_updatePatterns` for reusable patterns

**Do NOT modify this prompt file** - it is a template for creating plans, not for storing them.

---

## 7. Review and Adjust

Plan for periodic reviews and adjust steps as needed based on feedback or new information.

**Review Checklist:**
- Verify all tasks are saved via `aiSkeleton_*` tools
- Confirm #todos are tracked in progress system
- Ensure active context reflects current priorities
- Document any blockers or decisions

---

## Example

**Task:** Develop a new feature for the web application.

**Major Components:**
- Research requirements
- Design the feature
- Implement the code
- Test the feature
- Deploy the feature

**Actionable Steps & #todos:**
- #todo Review existing documentation
- #todo Conduct user interviews
- #todo Create wireframes
- #todo Write implementation code
- #todo Write unit tests
- #todo Deploy to staging

**Tools:**
- Research: Documentation tools, `aiSkeleton_updateContext` for context retrieval
- Design: Figma, `aiSkeleton_logDecision` for design decisions
- Implementation: Code editor, Copilot, `aiSkeleton_updatePatterns` for patterns
- Testing: Unit test framework, `aiSkeleton_updateProgress` for test strategies
- Deployment: CI/CD pipeline, `aiSkeleton_logDecision` for deployment logs

**Memory Management Usage:**
- Save plan: `aiSkeleton_updateProjectBrief`
- Track progress: `aiSkeleton_updateProgress`
- Log decisions: `aiSkeleton_logDecision`
- Update context: `aiSkeleton_updateContext`

---

*Use this template for each new task to ensure clarity, accountability, and progress tracking. All generated content should be saved via `aiSkeleton_*` tools, not to this template file.*

---

