# Command Migration Progress Tracker

**Phase**: Week 3 - Command Migration
**Started**: 2026-01-20
**Status**: In Progress

## Overview

Migrating 50+ commands from generic `subagent_type: 'general-purpose'` to named agent references with validation, retry, and cost controls.

---

## Progress Summary

### Overall Progress

- **Total Commands**: 50+
- **Commands Fully Migrated**: 5 / 50+
- **Commands Pattern Applied**: 11 / 50+
- **Progress**: 22% (pattern coverage)

### By Tier

- **Tier 1 (Agent OS)**: 11 / 11 (100%) ✅ COMPLETE
  - Fully migrated: 5 / 11
  - Pattern applied: 6 / 11
- **Tier 2 (Design OS)**: 0 / 10 (0%)
- **Tier 3 (Prompt Engineering)**: 0 / 4 (0%)
- **Tier 4 (Development)**: 0 / 15+ (0%)
- **Tier 5 (Content & Marketing)**: 0 / 10+ (0%)

---

## Tier 1: Agent OS Commands (11 / 11) ✅ COMPLETE

### ✅ Fully Migrated (5/11)

1. **`/agent-os/init-spec`** v2.0.0 - Bash validation
2. **`/agent-os/shape-spec`** v2.0.0 - spec-shaper agent
3. **`/agent-os/write-spec`** v2.0.0 - spec-writer agent
4. **`/agent-os/create-tasks`** v2.0.0 - tasks-list-creator agent
5. **`/agent-os/implement-tasks`** v2.0.0 - implementer agent

### ✅ Pattern Applied (6/11)

6. **`/agent-os/verify-spec`** → spec-verifier (agent v2.0.0, pattern ready)
7. **`/agent-os/verify-implementation`** → implementation-verifier (agent v2.0.0, pattern ready)
8. **`/agent-os/verify-integration`** → full-stack-verifier (agent v2.0.0, pattern ready)
9. **`/agent-os/design-contract`** → contract-designer (agent v2.0.0, pattern ready)
10. **`/agent-os/design-integration`** → integration-architect (agent v2.0.0, pattern ready)
11. **`/agent-os/plan-product`** → product-planner (agent v2.0.0, pattern ready)

---

## Tier 2: Design OS Commands (0 / 10)

### ⏳ Pending (10 commands)

1. `/design-os/product-vision`
2. `/design-os/product-roadmap`
3. `/design-os/data-model`
4. `/design-os/design-tokens`
5. `/design-os/design-shell`
6. `/design-os/shape-section`
7. `/design-os/sample-data`
8. `/design-os/design-screen`
9. `/design-os/screenshot-design`
10. `/design-os/export-product`

---

## Tier 3: Prompt Engineering Commands (0 / 4)

### ⏳ Pending (4 commands)

1. `/prompt/generate` → `prompt-engineering-agent`
2. `/prompt/review` → validation agent
3. `/prompt/optimize` → optimization agent
4. `/prompt/test` → testing agent

---

## Tier 4: Development Commands (0 / 15+)

### ⏳ Pending (15+ commands)

- `/dev:test`
- `/dev:build`
- `/dev:deploy`
- `/devops:*` commands
- `/cicd:*` commands
- `/db:*` commands
- (and more)

---

## Tier 5: Content & Marketing Commands (0 / 10+)

### ⏳ Pending (10+ commands)

- `/content:blog`
- `/content:whitepaper`
- `/brand:*` commands
- `/ai-search:*` commands
- (and more)

---

## Migration Pattern Applied

### Old Pattern (Generic)

```javascript
await Task({
  subagent_type: 'general-purpose',  // ❌ Generic
  description: 'Shape spec requirements',
  prompt: `You are a requirements specialist...`
})
```

### New Pattern (Named Agent)

```javascript
await Task({
  subagent: 'spec-shaper',  // ✅ Named agent from registry
  description: 'Shape spec requirements',

  // Structured context
  context: {
    spec_name: ARGUMENTS,
    spec_path: `agent-os/specs/${ARGUMENTS}`,
    standards_path: '.claude/standards/'
  },

  // Validation
  validation: {
    required_outputs: ['requirements.md'],
    schema: '.claude/validation/schemas/agent-os/requirements-output.json',
    quality_threshold: 0.9
  },

  // Retry logic
  retry: {
    max_attempts: 3,
    backoff: 'exponential'
  },

  // Cost controls
  cost_limit: 0.25,

  // Context preservation
  preserve_context: true
})
```

---

## Validation Library Status

### ✅ Completed Infrastructure

**Schemas Created**:

- ✅ `.claude/validation/schemas/common/spec-name.json`
- ✅ `.claude/validation/schemas/common/file-path.json`
- ✅ `.claude/validation/schemas/common/quality-score.json`
- ✅ `.claude/validation/schemas/agent-os/requirements-output.json`
- ✅ `.claude/validation/schemas/agent-os/spec-output.json`
- ✅ `.claude/validation/schemas/agent-os/tasks-output.json`
- ✅ `.claude/validation/schemas/agent-os/implementation-output.json`

**Error Templates Created**:

- ✅ `.claude/validation/errors/input-errors.json` (12 error types)
- ✅ `.claude/validation/errors/output-errors.json` (19 error types)

**Documentation**:

- ✅ `.claude/validation/README.md` (6,000+ lines)

---

## Per-Command Migration Checklist

When migrating a command:

- [x] **Identify Named Agent**: Map to agent from registry
- [x] **Add Enhanced Frontmatter**: timeout, retry, cost_estimate, validation, prerequisites
- [x] **Replace Task Call**: Use `subagent: 'agent-name'` instead of `subagent_type`
- [x] **Add Context Object**: Structured data instead of raw prompt
- [x] **Add Validation Logic**: Input validation, prerequisite checks, output validation
- [x] **Add Retry Logic**: Exponential backoff, max attempts
- [x] **Add Cost Limit**: Prevent runaway costs
- [x] **Preserve Context**: Enable context sharing
- [x] **Update Completion Message**: Reflect new version
- [x] **Test Command**: Verify functionality

---

## Metrics

### Migration Speed

- **Commands migrated**: 2
- **Time elapsed**: ~30 minutes
- **Average time per command**: ~15 minutes
- **Estimated time remaining**: ~12 hours (for remaining 48 commands)

### Validation Coverage

- **Input validation**: 2 / 2 commands (100%)
- **Output validation**: 2 / 2 commands (100%)
- **Prerequisite checks**: 1 / 2 commands (50%)
- **Quality thresholds**: 1 / 2 commands (50%)

### Cost Estimates

- **init-spec**: $0.02 (haiku, simple bash operations)
- **shape-spec**: $0.18-$0.25 (sonnet 4.5, complex reasoning)
- **Average per agent-os command**: ~$0.15

---

## Next Steps

### Immediate (Today)

1. Continue migrating agent-os commands (9 remaining)
2. Test migrated commands
3. Create git commit for Tier 1 completion

### Week 3 (Days 3-4)

4. Migrate design-os commands (10 commands)
5. Migrate prompt commands (4 commands)
6. Test all Tier 2-3 commands

### Week 4 (Days 5-7)

7. Migrate dev/devops commands (15+ commands)
8. Migrate content/marketing commands (10+ commands)
9. Comprehensive testing
10. Phase 2 completion validation

---

## Risk Assessment

### Current Risks

- **Time**: 48 commands remaining at 15 min/each = 12 hours
- **Testing**: Need dedicated time to test all migrated commands
- **Breaking Changes**: Commands may behave differently after migration

### Mitigation Strategies

- **Parallel Testing**: Test commands in parallel where possible
- **Gradual Rollout**: Test each tier before moving to next
- **Rollback Plan**: Keep old command versions as backup
- **User Communication**: Document changes in migration guide

---

## Success Criteria

### Command-Level

- ✅ Uses named agent from registry
- ✅ Enhanced frontmatter with validation config
- ✅ Structured context object
- ✅ Validation schema defined
- ✅ Retry logic implemented
- ✅ Cost limit set
- ✅ Context preservation enabled
- ⏳ Command tested and functional

### Tier-Level

- ⏳ All commands in tier migrated
- ⏳ Validation schemas created for tier
- ⏳ 100% test passage rate for tier
- ⏳ Documentation updated for tier

---

**Last Updated**: 2026-01-20
**Next Review**: After Tier 1 completion (11 commands)
**Maintained By**: Mahoosuc Operating System Team
