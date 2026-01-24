---
description: Intelligently route tasks to the optimal specialized agent
argument-hint: <task description>
model: claude-3-5-haiku-20241022
---

Analyze the task and automatically route to the optimal specialized agent.

## Task to Route

**Task**: $ARGUMENTS

## Step 1: Task Analysis

Analyze the task to determine:

1. **Task Category**:
   - Prompt Engineering (creating/optimizing prompts)
   - Zoho Integration (CRM/Mail/SMS operations)
   - Code Development (writing/refactoring code)
   - Documentation (creating/updating docs)
   - Architecture (system design, planning)
   - Security/Compliance (HIPAA, security audits)
   - Infrastructure (GCP, deployment, monitoring)
   - Testing/QA (test creation, quality assurance)
   - Data/Analytics (database, data pipelines)
   - Other

2. **Complexity Level** (use model-router logic):
   - Simple (Haiku-level task)
   - Medium (Sonnet-level task)
   - Complex (Opus-level task)

3. **Required Expertise**:
   - Domain knowledge needed
   - Technical skills required
   - Specialized frameworks/tools

## Step 2: Agent Matching

Based on the analysis, match to the optimal agent:

### Prompt Engineering Agents

- **prompt-engineering-agent** - Creating professional prompts (PromptCraft∞ Elite)
- **documentation-expert-agent** - Creating documentation
- **model-router** - Analyzing task complexity for model selection

### Integration & Automation Agents

- **agent-router** - Meta-routing and task classification
- **zoho-integration-agent** - Zoho CRM/Mail/SMS operations (if created)
- **workflow-orchestrator** - Multi-step workflow coordination (if created)

### Development Agents

- **code-reviewer** - Code review and analysis
- **frontend-architect** - Frontend architecture and React/Vue/Angular
- **design-system-architect** - Design systems and component libraries
- **responsive-design-specialist** - Mobile-first and responsive design
- **frontend-qa-engineer** - Frontend testing strategies
- **playwright-test-architect** - Playwright test automation
- **accessibility-auditor** - WCAG compliance and accessibility

### Infrastructure & DevOps Agents

- **gcp-infrastructure-architect** - GCP infrastructure as code (Terraform)
- **gcp-monitoring-sre** - GCP monitoring and observability
- **serverless-architect** - Cloud Functions and Cloud Run
- **cicd-pipeline-architect** - CI/CD pipelines and GitOps
- **devops-github-docker-agent** - GitHub operations and Docker
- **github-ops-expert** - GitHub repository management

### Security & Compliance Agents

- **gcp-security-compliance** - GCP security and compliance
- **healthcare-security-compliance** - HIPAA and healthcare compliance
- **healthcare-api-integration-expert** - Healthcare API and FHIR

### Data & Analytics Agents

- **gcp-database-architect** - Cloud SQL, Firestore, Spanner
- **healthcare-database-expert** - Healthcare data architecture
- **gcp-data-pipeline-engineer** - Data pipelines and BigQuery

### Specialized Domain Agents

- **voice-ai-architect** - Voice AI and conversational interfaces
- **hospitality-voice-architect** - Hotel/hospitality voice systems
- **n8n-workflow-developer** - n8n workflow automation

### Testing & Quality Agents

- **qa-testing-engineer** - Comprehensive testing strategies
- **ux-testing-specialist** - UX evaluation with Playwright
- **playwright-test-analyzer** - Test suite analysis and optimization

### Research & Analysis Agents

- **ux-research-analyst** - UX research and user analysis
- **mermaid-architect** - Visual documentation and diagrams

### Troubleshooting & Optimization Agents

- **gcp-troubleshooting-specialist** - GCP issue diagnosis
- **web-performance-optimizer** - Web performance optimization
- **gcp-cost-optimizer** - GCP cost analysis and optimization

## Step 3: Routing Decision

Based on the task analysis, I will route this task to:

**Selected Agent**: [agent-name]

**Reasoning**:

- Task Category: [category]
- Complexity: [simple/medium/complex]
- Required Expertise: [expertise areas]
- Why this agent: [2-3 sentence justification]

**Alternative Agents Considered**:

- [agent-2]: [why not selected]
- [agent-3]: [why not selected]

## Step 4: Task Handoff

I will now invoke the selected agent using the Task tool.

**Handoff Details**:

- Agent: [agent-name]
- Task: [reformulated task optimized for this agent]
- Expected Output: [what the agent should deliver]
- Context: [any relevant context from this conversation]

---

**Routing to: [agent-name]**

[Use Task tool to invoke the selected agent with the appropriate prompt]

## Routing Rules & Guidelines

### Prompt Engineering Tasks

**Route to**: prompt-engineering-agent

- Creating new prompts
- Optimizing existing prompts
- Designing agent personas
- Implementing prompt frameworks (CoT, ReAct, etc.)

### Zoho Operations

**Route to**: Appropriate Zoho command

- Use `/zoho/create-lead` for lead creation
- Use `/zoho/send-email` for email operations
- Use `/zoho/send-sms` for SMS operations
- Complex Zoho workflows → workflow-orchestrator

### Code Development

**Route by technology**:

- Frontend (React/Vue/Angular) → frontend-architect
- Testing → frontend-qa-engineer or qa-testing-engineer
- Design systems → design-system-architect
- Accessibility → accessibility-auditor

### Infrastructure

**Route by platform**:

- GCP infrastructure → gcp-infrastructure-architect
- Monitoring/observability → gcp-monitoring-sre
- Serverless → serverless-architect
- CI/CD → cicd-pipeline-architect

### Security & Compliance

**Route by domain**:

- Healthcare/HIPAA → healthcare-security-compliance
- General GCP security → gcp-security-compliance
- Healthcare APIs → healthcare-api-integration-expert

### Ambiguous Tasks

If task could match multiple agents:

1. Use **agent-router** agent to make meta-routing decision
2. Consider complexity (simpler tasks → more focused agents)
3. Consider context (what's the broader goal?)
4. When in doubt, ask user to clarify

## Quality Checks

Before routing:

- [ ] Task clearly understood
- [ ] Agent selection justified
- [ ] Complexity level assessed
- [ ] Alternative agents considered
- [ ] Expected output defined
- [ ] Context provided to receiving agent

## Example Routing Decisions

### Example 1: Prompt Engineering

**Task**: "Create a customer support agent for healthcare"
**Route to**: prompt-engineering-agent
**Reasoning**: Classic prompt creation task requiring PromptCraft∞ Elite workflow

### Example 2: Zoho CRM

**Task**: "Add a new lead to Zoho CRM"
**Route to**: /zoho/create-lead command
**Reasoning**: Direct Zoho operation with established slash command

### Example 3: Frontend Development

**Task**: "Build a responsive dashboard component"
**Route to**: frontend-architect OR responsive-design-specialist
**Reasoning**: Could use frontend-architect for overall structure, then responsive-design-specialist for mobile optimization

### Example 4: Complex Multi-Domain

**Task**: "Design a HIPAA-compliant patient portal with voice AI"
**Route to**: Multiple agents in sequence:

1. healthcare-security-compliance - Define compliance requirements
2. voice-ai-architect - Design voice interface
3. gcp-infrastructure-architect - Design infrastructure
4. frontend-architect - Build web interface

## Notes

- This command uses Haiku model for fast routing analysis
- Complex tasks may require multiple agents (orchestration)
- Some tasks can be parallelized across agents
- Always provide clear handoff context to receiving agents
- Track routing decisions for optimization

## Example Usage

```
/route Create a new prompt for lead qualification
# Routes to prompt-engineering-agent

/route Set up GCP monitoring for our healthcare app
# Routes to gcp-monitoring-sre + healthcare-security-compliance

/route Fix accessibility issues in the checkout flow
# Routes to accessibility-auditor
```
