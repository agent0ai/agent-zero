# Phase 2: Command Migration Plan

**Version**: 1.0.0
**Created**: 2026-01-20
**Status**: In Progress

## Overview

Migrate 50+ critical commands from generic `subagent_type: 'general-purpose'` pattern to modern named agent references with validation, retry logic, and cost controls.

---

## Priority Command Categories

### Tier 1: Critical Workflows (11 commands)

**Agent OS Commands** (11 commands):

1. `/agent-os/init-spec` → `spec-initializer`
2. `/agent-os/shape-spec` → `spec-shaper`
3. `/agent-os/write-spec` → `spec-writer`
4. `/agent-os/verify-spec` → `spec-verifier`
5. `/agent-os/design-contract` → `contract-designer`
6. `/agent-os/design-integration` → `integration-architect`
7. `/agent-os/create-tasks` → `tasks-list-creator`
8. `/agent-os/implement-tasks` → `implementer`
9. `/agent-os/verify-implementation` → `implementation-verifier`
10. `/agent-os/verify-integration` → `full-stack-verifier`
11. `/agent-os/plan-product` → `product-planner`

**Priority**: HIGHEST (complete spec-driven development workflow)

---

### Tier 2: Design & UI Commands (10 commands)

**Design OS Commands** (assumed ~10 commands):

- `/design-os/product-vision`
- `/design-os/product-roadmap`
- `/design-os/data-model`
- `/design-os/design-tokens`
- `/design-os/design-shell`
- `/design-os/shape-section`
- `/design-os/sample-data`
- `/design-os/design-screen`
- `/design-os/screenshot-design`
- `/design-os/export-product`

**Priority**: HIGH (product design workflow)

---

### Tier 3: Prompt Engineering Commands (4 commands)

1. `/prompt/generate` → `prompt-engineering-agent` (from meta-prompts)
2. `/prompt/review` → validation agent
3. `/prompt/optimize` → optimization agent
4. `/prompt/test` → testing agent

**Priority**: HIGH (core capability)

---

### Tier 4: Development Commands (15+ commands)

- `/dev:test`
- `/dev:build`
- `/dev:deploy`
- `/devops:*` commands
- `/cicd:*` commands
- `/db:*` commands

**Priority**: MEDIUM

---

### Tier 5: Content & Marketing (10+ commands)

- `/content:blog`
- `/content:whitepaper`
- `/brand:*` commands
- `/ai-search:*` commands

**Priority**: MEDIUM

---

## Migration Pattern

### Old Pattern (Generic)

```markdown
---
description: Gather detailed requirements
argument-hint: <spec-name>
allowed-tools: Task, Read, Write
---

await Task({
  subagent_type: 'general-purpose',  # ❌ Generic
  description: 'Shape spec requirements',
  prompt: `
    You are a requirements specialist...
    [Long prompt with instructions]
  `
})
```

### New Pattern (Named Agent)

```markdown
---
description: Gather detailed requirements through targeted questions and visual analysis
argument-hint: <spec-name>
allowed-tools: Task, Read, Write, AskUserQuestion
model: claude-sonnet-4-5
timeout: 1800
retry: 3
cost_estimate: 0.18

# Validation
validation:
  input:
    spec_name:
      type: string
      pattern: '^[a-z0-9-]+$'
  output:
    required_files:
      - 'agent-os/specs/${spec_name}/requirements.md'
    min_file_size: 1000

# Prerequisites
prerequisites:
  - command: /agent-os/init-spec
    file_exists: 'agent-os/specs/${spec_name}/idea.md'
---

await Task({
  subagent: 'spec-shaper',  # ✅ Named agent from registry
  context: {
    spec_name: ARGUMENTS,
    spec_path: `agent-os/specs/${ARGUMENTS}`,
    standards_path: '.claude/standards/',
    visuals_path: `agent-os/specs/${ARGUMENTS}/visuals/`
  },
  validation: {
    required_outputs: ['requirements.md'],
    schema: requirementsSchema,
    quality_threshold: 0.9
  },
  retry: {
    max_attempts: 3,
    on_failure: 'notify-user',
    backoff: 'exponential'
  },
  cost_limit: 0.25,
  preserve_context: true
})
```

---

## Migration Checklist

### Per Command Migration

- [ ] **Identify Named Agent**: Map to agent from registry
- [ ] **Add Enhanced Frontmatter**: timeout, retry, cost_estimate, validation, prerequisites
- [ ] **Replace Task Call**: Use `subagent: 'agent-name'` instead of `subagent_type`
- [ ] **Add Context Object**: Structured data instead of raw prompt
- [ ] **Add Validation Schema**: Input/output validation
- [ ] **Add Retry Logic**: Exponential backoff, max attempts
- [ ] **Add Cost Limit**: Prevent runaway costs
- [ ] **Preserve Context**: Enable context sharing
- [ ] **Update Documentation**: Reflect new pattern
- [ ] **Test Command**: Verify functionality

---

## Validation Library Structure

```
.claude/validation/
├── README.md                    # Validation library guide
├── schemas/                     # Reusable validation schemas
│   ├── common/
│   │   ├── spec-name.json      # Spec name validation
│   │   ├── file-path.json      # File path validation
│   │   └── arguments.json      # Common argument patterns
│   ├── agent-os/
│   │   ├── requirements-output.json
│   │   ├── spec-output.json
│   │   ├── tasks-output.json
│   │   └── implementation-output.json
│   ├── design-os/
│   │   ├── design-tokens-output.json
│   │   ├── component-output.json
│   │   └── export-output.json
│   └── templates/
│       ├── input-validation.template.json
│       └── output-validation.template.json
├── validators/                  # Validation functions
│   ├── input-validators.js
│   ├── output-validators.js
│   └── schema-validators.js
└── errors/                      # Error message templates
    ├── input-errors.json
    └── output-errors.json
```

---

## Implementation Plan

### Week 3: Foundation (Days 1-2)

**Day 1**:

1. Create validation library structure
2. Migrate 11 agent-os commands
3. Create agent-os validation schemas

**Day 2**:
4. Test agent-os commands
5. Create reusable validation templates
6. Document migration patterns

### Week 3: Expansion (Days 3-4)

**Day 3**:
7. Migrate design-os commands (10 commands)
8. Create design-os validation schemas
9. Test design-os commands

**Day 4**:
10. Migrate prompt commands (4 commands)
11. Migrate dev/devops commands (15 commands)
12. Create validation schemas

### Week 4: Testing & Optimization (Days 5-7)

**Day 5**:
13. Comprehensive testing of all migrated commands
14. Fix any issues found
15. Optimize slow commands

**Day 6**:
16. Migrate content/marketing commands (10 commands)
17. Create final validation schemas
18. Performance benchmarking

**Day 7**:
19. Documentation updates
20. Migration guide creation
21. Phase 2 completion validation

---

## Success Criteria

### Command-Level Success

- ✅ Command uses named agent from registry
- ✅ Enhanced frontmatter with timeout, retry, cost, validation
- ✅ Context object with structured data
- ✅ Validation schema defined
- ✅ Retry logic implemented
- ✅ Cost limit set
- ✅ Context preservation enabled
- ✅ Command tested and functional

### Phase-Level Success

- ✅ 50+ commands migrated
- ✅ Validation library created
- ✅ 100% test passage rate
- ✅ Documentation complete
- ✅ Migration guide published

---

## Metrics to Track

### Migration Metrics

- Commands migrated: 0 / 50+
- Validation schemas created: 0 / 20+
- Test passage rate: N/A
- Average migration time per command: TBD

### Performance Metrics

- Command success rate before: TBD
- Command success rate after: Target 95%+
- Average cost per command: TBD
- Cost reduction: Target 25%

---

## Risk Mitigation

### Risks

1. **Breaking Changes**: Commands may behave differently
   - **Mitigation**: Comprehensive testing, gradual rollout

2. **Performance Degradation**: New patterns may be slower
   - **Mitigation**: Benchmark before/after, optimize as needed

3. **Cost Increases**: Named agents may cost more
   - **Mitigation**: Cost limits, budget alerts

4. **User Confusion**: New patterns may confuse users
   - **Mitigation**: Clear documentation, migration guide

---

## Current Status

**Phase**: Week 3, Day 1
**Progress**: 0 / 50+ commands migrated
**Next Steps**:

1. Create validation library structure
2. Begin agent-os command migration

---

**Last Updated**: 2026-01-20
**Maintained By**: Mahoosuc Operating System Team
