---
description: Create project constitution with governance principles, constraints, and quality gates
allowed-tools: [Bash, Read, Write, AskUserQuestion]
argument-hint: "[project-name] [--template <type>] [--from-design <design-id>]"
---

# /spec-kit:constitution - Create Project Constitution

Create a project constitution that defines governance principles, constraints, quality gates, and technology preferences.

## Overview

Constitutions provide a governance framework for projects:

- **Principles**: Core values and decision-making guidelines
- **Constraints**: Hard rules that must be followed
- **Quality Gates**: Criteria for success and validation
- **Preferred Stack**: Technology preferences and standards

## Execution Steps

### Step 1: Determine Creation Method

Ask the user to choose the creation method:

**Question 1: How would you like to create the constitution?**

- **From Template** (Recommended) - Use one of 10 built-in templates
- **Interactive Creation** - Build from scratch with guided questions
- **From Existing Design** - Extract governance from DEVB design

### Step 2a: Template-Based Creation (if chosen)

Present available templates:

1. **SaaS Best Practices** - Security-first, multi-tenant, scalable SaaS
2. **RESTful API Standards** - Enterprise-grade REST APIs with OpenAPI
3. **Microservices Architecture** - Service-oriented, fault-tolerant systems
4. **Mobile App Standards** - iOS/Android with offline-first approach
5. **Fintech Compliance** - PCI DSS, SOC 2, fraud detection
6. **Healthcare HIPAA** - PHI protection, audit trails, BAAs
7. **E-commerce Platform** - Payment security, inventory management
8. **Event-Driven Architecture** - Event sourcing, CQRS, idempotency
9. **Enterprise Application** - 99.9% uptime, DR, compliance
10. **Startup MVP** - Speed to market, cost efficiency

**Ask:** "Which template would you like to use? (1-10)"

**Then ask for customizations:**

- Project name (override template name)
- Additional principles
- Additional constraints
- Specific technology stack preferences

**Call API:**

```bash
curl -X POST http://localhost:3000/api/constitutions/templates/{type}/apply \
  -H "Content-Type: application/json" \
  -d '{
    "name": "{project_name}",
    "description": "{description}",
    "principles": [{additional_principles}],
    "constraints": [{additional_constraints}],
    "preferred_stack": {technology_preferences},
    "created_by": "{user_id}"
  }'
```

### Step 2b: Interactive Creation (if chosen)

Collect information through guided questions:

**1. Project Overview**

- Project name
- Description (1-2 sentences)
- Domain (api, event-driven, graphql, general)

**2. Core Principles** (3-5 principles)
Ask: "What are your core principles?" (examples: Security First, Performance, Cost Efficiency, Developer Experience)

For each principle, collect:

- Title (e.g., "Security First")
- Description (e.g., "All data encrypted at rest and in transit")
- Priority (must, should, could)

**3. Constraints** (3-5 constraints)
Ask: "What are your hard constraints?" (examples: No direct DB access from frontend, All APIs must use authentication)

For each constraint, collect:

- Category (architecture, security, performance, cost)
- Rule description
- Enforcement level (hard, soft)

**4. Quality Gates** (3-5 gates)
Ask: "What quality gates must be met?" (examples: 80% test coverage, Zero critical vulnerabilities)

For each gate, collect:

- Name
- Criteria
- Threshold (if numeric)
- Automated (yes/no)

**5. Technology Stack**
Ask: "What technologies are preferred/required?"

- Languages (e.g., TypeScript, Python, Go)
- Frameworks (e.g., React, Next.js, FastAPI)
- Databases (e.g., PostgreSQL, Redis)
- Cloud providers (e.g., AWS, GCP, Azure)
- Tools (e.g., Docker, Kubernetes, GitHub Actions)

**Call API:**

```bash
curl -X POST http://localhost:3000/api/constitutions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "{project_name}",
    "description": "{description}",
    "principles": [{collected_principles}],
    "constraints": [{collected_constraints}],
    "quality_gates": [{collected_gates}],
    "preferred_stack": {collected_stack},
    "created_by": "{user_id}"
  }'
```

### Step 2c: From Existing Design (if chosen)

Ask: "Enter the design ID to extract governance from:"

1. Fetch the design specification
2. Extract relevant governance information
3. Generate constitution via spec-kit CLI

**Use spec-kit bridge:**

```bash
curl -X POST http://localhost:3000/api/spec-kit/constitution \
  -H "Content-Type: application/json" \
  -d '{
    "projectName": "{design_title}",
    "description": "{design_description}",
    "domain": "{domain_type}"
  }'
```

Then parse the spec-kit output and create constitution via API.

### Step 3: Display Constitution Summary

After creation, display a comprehensive summary:

```
✅ Constitution Created Successfully!

Constitution ID: const-abc-123
Name: {project_name}
Template: {template_type or "Custom"}

📋 Summary:
• Principles: {count} defined
• Constraints: {count} defined
• Quality Gates: {count} defined
• Technology Stack: {languages_count} languages, {frameworks_count} frameworks

🔑 Key Principles:
1. {principle_1_title}: {principle_1_description}
2. {principle_2_title}: {principle_2_description}
3. {principle_3_title}: {principle_3_description}

⚠️ Critical Constraints:
1. {constraint_1}
2. {constraint_2}
3. {constraint_3}

✓ Quality Gates:
1. {gate_1}: {criteria_1}
2. {gate_2}: {criteria_2}

💻 Preferred Stack:
Languages: {languages_list}
Frameworks: {frameworks_list}
Databases: {databases_list}

📁 Next Steps:
• Link to design: /spec-kit:constitution const-abc-123 --link-design <design-id>
• Create design with constitution: /design:solution --constitution const-abc-123
• View full constitution: /spec-kit:constitution const-abc-123 --view
• Edit constitution: /spec-kit:constitution const-abc-123 --edit
```

### Step 4: Optional Actions

Ask if the user wants to:

- Link this constitution to an existing design
- Create a new design with this constitution
- Export constitution to file
- Create a child constitution (inherit from this one)

## Advanced Features

### View Constitution

```bash
/spec-kit:constitution <constitution-id> --view
```

Fetch and display full constitution details.

### Edit Constitution

```bash
/spec-kit:constitution <constitution-id> --edit
```

Interactive editing of principles, constraints, or stack.

### Create Version

```bash
/spec-kit:constitution <constitution-id> --version
```

Create a new version with updates while preserving history.

### Link to Design

```bash
/spec-kit:constitution <constitution-id> --link-design <design-id>
```

Link constitution to an existing design specification.

### Export Constitution

```bash
/spec-kit:constitution <constitution-id> --export <path>
```

Export constitution to markdown file.

## Error Handling

**If template not found:**
Display available templates and ask user to choose again.

**If API call fails:**
Show error message and suggest:

1. Check backend is running
2. Verify spec-kit is installed
3. Try simpler constitution first

**If validation fails:**
Show validation errors and ask user to correct.

## Example Usage

### Example 1: SaaS Application

```
User: /spec-kit:constitution "MyApp"
Assistant: How would you like to create the constitution?
User: From Template
Assistant: Which template? (1-10)
User: 1 (SaaS Best Practices)
Assistant: ✅ Constitution created! const-abc-123
```

### Example 2: Custom Healthcare App

```
User: /spec-kit:constitution "HealthPortal" --template healthtech
Assistant: Customizing Healthcare HIPAA template...
  Additional principles? GDPR compliance, User privacy
  Additional constraints? All PHI must be encrypted with AES-256
Assistant: ✅ Constitution created! const-def-456
```

### Example 3: From Existing Design

```
User: /spec-kit:constitution --from-design design-xyz-789
Assistant: Extracting governance from design...
Assistant: ✅ Constitution created! const-ghi-789
```

## Success Criteria

✅ Constitution created with valid principles, constraints, and quality gates
✅ Constitution stored in database with ID
✅ User understands how to use the constitution
✅ Clear next steps provided

## Notes

- Constitutions can be versioned (use --version flag)
- Constitutions support inheritance (use --parent flag)
- Multiple constitutions can be linked to one design
- Templates are a great starting point - customize as needed
- Constitution compliance is checked during design validation
