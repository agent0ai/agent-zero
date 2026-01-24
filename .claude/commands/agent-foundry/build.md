---
description: Build agent implementation with skills, tools, and integration patterns
allowed-tools: [Bash, Read, Write, Grep, Task]
argument-hint: "<agent-name> [--with-tests]"
---

# /agent-foundry/build - Build Agent Implementation

Transform agent design into working implementation with skills registration and tool integration.

## Overview

Creates operational agent by:

1. Registering agent skills in Skills Registry
2. Generating required commands
3. Creating integration points
4. Setting up routing logic
5. Implementing tool access patterns

## Process

### Step 1: Load Agent Design

Read agent specification from `.claude/agents/{category}/{agent-name}.md`:

```bash
# Extract from agent file:
- Agent name
- Category/domain
- Capabilities list
- Required tools
- Input/output protocols
- Dependencies
```

### Step 2: Skills Registration

For each capability, create a skill definition:

```typescript
// Example: database-architect capabilities
const schemaDesignSkill: Skill = {
  id: 'design-schema',
  name: 'Database Schema Designer',
  category: 'db',
  description: 'Design optimal database schemas with multi-tenant support',
  capabilities: [
    'Analyze data requirements',
    'Design normalized schemas',
    'Create migration scripts',
    'Optimize for performance'
  ],
  requiredTools: ['Read', 'Write', 'Bash'],
  inputSchema: z.object({
    requirements: z.string().describe('Business requirements'),
    constraints: z.array(z.string()).optional(),
    existingSchema: z.string().optional()
  }),
  examples: [{
    input: '--requirements "Multi-tenant SaaS with users, organizations, subscriptions"',
    output: 'Generated schema with proper isolation and indexing',
    explanation: 'Design multi-tenant schema'
  }],
  complexity: 'expert',
  tags: ['database', 'architecture', 'schema']
}

skillsRegistry.register(schemaDesignSkill)
```

### Step 3: Generate Commands

Auto-generate slash commands for each skill:

**Result**:

- `.claude/commands/db/design-schema.md`
- `.claude/commands/db/optimize-queries.md`
- `.claude/commands/db/create-migration.md`
- etc.

Each command is immediately available via:

```bash
/db/design-schema --requirements "..."
/db/optimize-queries --table users
/db/create-migration --name add_user_roles
```

### Step 4: Agent Routing Integration

Add routing logic to `/agent/route`:

```typescript
// Add to agent router
function routeTask(task: string): Agent {
  const keywords = extractKeywords(task)

  // New agent routing
  if (keywords.includes('schema') || keywords.includes('database')) {
    return 'database-architect'
  }
  if (keywords.includes('security') || keywords.includes('vulnerability')) {
    return 'security-auditor'
  }
  if (keywords.includes('cost') || keywords.includes('optimize-billing')) {
    return 'cost-optimizer'
  }

  // ... existing routing
}
```

**Update**: `.claude/CLAUDE.md` with new agent routing rules

### Step 5: Tool Access Patterns

Define how agent uses tools:

```typescript
// Example: Security Auditor tool usage
const toolPatterns = {
  agent: 'security-auditor',
  tools: {
    'Bash': {
      purpose: 'Run security scanning tools',
      examples: [
        'npm audit --json',
        'snyk test --severity-threshold=high',
        'trivy image myapp:latest'
      ]
    },
    'Read': {
      purpose: 'Analyze code for vulnerabilities',
      patterns: [
        'Read dependencies files (package.json, requirements.txt)',
        'Read configuration files for secrets',
        'Read source code for security patterns'
      ]
    },
    'Write': {
      purpose: 'Generate security reports',
      outputs: [
        'Security audit report',
        'Vulnerability remediation plan',
        'Compliance checklist'
      ]
    }
  }
}
```

### Step 6: Integration Tests

Generate test suite for agent:

```typescript
// .claude/tests/agents/{agent-name}.test.ts
describe('Database Architect Agent', () => {
  it('should design multi-tenant schema', async () => {
    const result = await agent.execute({
      capability: 'design-schema',
      input: {
        requirements: 'Multi-tenant SaaS app',
        constraints: ['PostgreSQL', 'UUID primary keys']
      }
    })

    expect(result.schema).toHaveProperty('organizations')
    expect(result.schema.users).toHaveProperty('organization_id')
    expect(result.migrations).toBeArray()
  })

  it('should optimize query performance', async () => {
    const result = await agent.execute({
      capability: 'optimize-queries',
      input: {
        query: 'SELECT * FROM users WHERE email = $1',
        table: 'users'
      }
    })

    expect(result.suggestions).toInclude('Add index on users(email)')
    expect(result.optimizedQuery).toBeDefined()
  })
})
```

### Step 7: Documentation Generation

Create comprehensive documentation:

**Files Generated**:

1. **Agent README** - `.claude/agents/{category}/{agent-name}/README.md`

   ```markdown
   # Database Architect Agent

   ## Overview
   {agent description}

   ## Available Commands
   - `/db/design-schema` - Design database schemas
   - `/db/optimize-queries` - Optimize SQL queries
   - `/db/create-migration` - Generate migrations

   ## Usage Examples
   {examples from design spec}

   ## Integration with Other Agents
   - Works with `implementer` for feature development
   - Collaborates with `security-auditor` for compliance
   - Feeds into `performance-optimizer` for tuning
   ```

2. **API Reference** - `.claude/agents/{category}/{agent-name}/API.md`
   - Input schemas for each capability
   - Output formats
   - Error handling
   - Rate limits (if applicable)

3. **Examples** - `.claude/agents/{category}/{agent-name}/examples/`
   - Real-world usage scenarios
   - Common workflows
   - Troubleshooting guide

### Step 8: Deployment Checklist

Verify before marking as ready:

```yaml
deployment_checklist:
  skills_registered: true
  commands_generated: true
  routing_updated: true
  tests_created: true
  documentation_complete: true
  examples_provided: true
  quality_gates_passed: true
```

### Step 9: Build Summary

```
✓ Agent Build Complete: {agent-name}

📦 Generated Components:
   Skills: {count}
   Commands: {count}
   Tests: {count}
   Docs: {count}

🎯 Available Commands:
   {list of generated commands}

🔗 Integration Points:
   - Agent routing updated
   - Skills registry populated
   - Tool patterns configured

📊 Quality Metrics:
   Test coverage: {percentage}
   Documentation: {percentage}
   Examples: {count}

🚀 Next Steps:
   1. Run: /agent-foundry/test {agent-name}
   2. Run: /agent-foundry/train {agent-name}
   3. Run: /agent-foundry/evaluate {agent-name}

⚠️  Important:
   Commands are now available but agent needs training
   before production deployment.
```

## Build Modes

### Mode 1: Minimal Build

- Core skills only
- Basic routing
- Essential docs

### Mode 2: Standard Build (Default)

- All designed skills
- Full routing integration
- Complete documentation
- Integration tests

### Mode 3: Complete Build (--with-tests)

- Everything in Standard
- Comprehensive test suite
- Performance benchmarks
- Usage analytics setup

## Usage Examples

### Example 1: Build Database Architect

```bash
/agent-foundry/build database-architect --with-tests
```

Output:

- 8 skills registered
- 8 commands generated
- 12 test cases created
- Full documentation

### Example 2: Build Security Auditor

```bash
/agent-foundry/build security-auditor
```

Creates security scanning agent with OWASP compliance checks.

### Example 3: Build Cost Optimizer

```bash
/agent-foundry/build cost-optimizer
```

Implements cloud cost analysis and optimization capabilities.

## Quality Gates

✅ All skills registered successfully
✅ Commands generated without errors
✅ Routing logic doesn't conflict
✅ Tool patterns are valid
✅ Tests compile and pass
✅ Documentation is complete
✅ No circular dependencies

## Troubleshooting

### Issue: Skill registration fails

**Solution**: Check for duplicate skill IDs, validate input schemas

### Issue: Command generation errors

**Solution**: Verify category directory exists, check file permissions

### Issue: Routing conflicts

**Solution**: Review keyword matching, adjust priority weights

### Issue: Tool access denied

**Solution**: Verify tools are in allowed-tools list for category
