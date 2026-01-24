# Command Validation Library

**Version**: 1.0.0
**Created**: 2026-01-20
**Purpose**: Centralized validation schemas and validators for all slash commands

## Overview

This validation library provides reusable validation schemas, validators, and error handlers for all slash commands in the Mahoosuc Operating System. It ensures consistent input validation, output verification, and error handling across 50+ commands.

## Architecture

```text
.claude/validation/
├── README.md                    # This file
├── schemas/                     # JSON Schema validation files
│   ├── common/                  # Shared validation patterns
│   ├── agent-os/                # Agent OS command schemas
│   ├── design-os/               # Design OS command schemas
│   └── templates/               # Schema templates
├── validators/                  # Validation functions
└── errors/                      # Error message templates
```

## Validation Layers

Commands use **3 layers of validation**:

### 1. Input Validation

Validates command arguments before execution.

```yaml
validation:
  input:
    spec_name:
      type: string
      pattern: '^[a-z0-9-]+$'
      min_length: 3
      max_length: 50
```

### 2. Execution Validation

Validates intermediate steps during execution.

```yaml
validation:
  execution:
    steps:
      - name: file_created
        check: file_exists
        path: 'agent-os/specs/${spec_name}/requirements.md'
```

### 3. Output Validation

Validates final outputs and artifacts.

```yaml
validation:
  output:
    required_files:
      - 'agent-os/specs/${spec_name}/requirements.md'
    min_file_size: 1000
    quality_threshold: 0.9
```

## Common Schemas

### Spec Name Validation

```json
{
  "type": "string",
  "pattern": "^[a-z0-9-]+$",
  "minLength": 3,
  "maxLength": 50,
  "description": "Feature/spec name (lowercase, alphanumeric, hyphens)"
}
```

### File Path Validation

```json
{
  "type": "string",
  "pattern": "^[a-zA-Z0-9/_.-]+$",
  "description": "Valid file path (no special characters)"
}
```

### Quality Score Validation

```json
{
  "type": "number",
  "minimum": 0,
  "maximum": 1,
  "description": "Quality score (0.0 to 1.0)"
}
```

## Agent-OS Schemas

### Requirements Output Schema

Validates output from `/agent-os/shape-spec`.

**File**: `schemas/agent-os/requirements-output.json`

**Required files**:

- `agent-os/specs/{spec_name}/requirements.md`

**Content validation**:

- Minimum 1000 characters
- Must contain sections: User Stories, Acceptance Criteria, Technical Requirements
- Must reference at least 1 standard from `.claude/standards/`

### Specification Output Schema

Validates output from `/agent-os/write-spec`.

**File**: `schemas/agent-os/spec-output.json`

**Required files**:

- `agent-os/specs/{spec_name}/spec.md`

**Content validation**:

- Minimum 2000 characters
- Must contain sections: Overview, Architecture, API Design, Database Schema, Frontend Components
- Must include at least 1 diagram (mermaid code block)

### Tasks Output Schema

Validates output from `/agent-os/create-tasks`.

**File**: `schemas/agent-os/tasks-output.json`

**Required files**:

- `agent-os/specs/{spec_name}/tasks.md`

**Content validation**:

- Minimum 5 tasks
- Each task must have: description, acceptance criteria, dependencies
- Must include testing tasks

### Implementation Output Schema

Validates output from `/agent-os/implement-tasks`.

**File**: `schemas/agent-os/implementation-output.json`

**Required artifacts**:

- All files listed in tasks.md
- Test files with >80% coverage
- All tasks marked as completed

## Design-OS Schemas

### Design Tokens Output Schema

Validates output from `/design-os/design-tokens`.

**File**: `schemas/design-os/design-tokens-output.json`

**Required files**:

- `design-os/{product}/design-tokens.json`

**Content validation**:

- Must contain: colors, typography, spacing, breakpoints
- Colors must use Tailwind CSS format
- Typography must reference Google Fonts

### Component Output Schema

Validates output from `/design-os/design-screen`.

**File**: `schemas/design-os/component-output.json`

**Required files**:

- React component files (.tsx)
- Component styles
- Sample data file

**Content validation**:

- Components must use TypeScript
- Must import design tokens
- Must include accessibility attributes (ARIA)

## Validator Functions

### Input Validators

**File**: `validators/input-validators.js`

Functions:

- `validateSpecName(name)` - Validates spec/feature name
- `validateFilePath(path)` - Validates file path
- `validateEnum(value, allowed)` - Validates enum values
- `validatePattern(value, regex)` - Validates regex patterns

### Output Validators

**File**: `validators/output-validators.js`

Functions:

- `validateFileExists(path)` - Checks file exists
- `validateFileSize(path, minSize)` - Checks minimum file size
- `validateFileContent(path, schema)` - Validates file content against schema
- `validateQualityScore(score, threshold)` - Checks quality threshold

### Schema Validators

**File**: `validators/schema-validators.js`

Functions:

- `validateAgainstSchema(data, schema)` - JSON Schema validation
- `generateValidationReport(results)` - Formats validation report
- `checkPrerequisites(prerequisites)` - Validates command prerequisites

## Error Templates

### Input Errors

**File**: `errors/input-errors.json`

```json
{
  "INVALID_SPEC_NAME": {
    "message": "Invalid spec name: {{name}}. Must be lowercase, alphanumeric, hyphens only.",
    "hint": "Try: user-authentication, payment-flow, dashboard-ui",
    "severity": "error"
  },
  "MISSING_ARGUMENT": {
    "message": "Missing required argument: {{arg_name}}",
    "hint": "Usage: {{command}} {{args}}",
    "severity": "error"
  }
}
```

### Output Errors

**File**: `errors/output-errors.json`

```json
{
  "FILE_NOT_FOUND": {
    "message": "Required file not created: {{file_path}}",
    "hint": "Agent should have created this file. Check agent logs.",
    "severity": "error",
    "recovery": "Re-run command with --force flag"
  },
  "QUALITY_THRESHOLD_NOT_MET": {
    "message": "Quality score {{score}} below threshold {{threshold}}",
    "hint": "Review output for completeness and accuracy",
    "severity": "warning",
    "recovery": "Run /agent-os/verify-spec to identify issues"
  }
}
```

## Usage Examples

### In Command Frontmatter

```yaml
---
description: Gather detailed requirements
argument-hint: <spec-name>
allowed-tools: Task, Read, Write, AskUserQuestion
model: claude-sonnet-4-5
timeout: 1800
retry: 3
cost_estimate: 0.18

# Input Validation
validation:
  input:
    spec_name:
      schema: .claude/validation/schemas/common/spec-name.json
      required: true

  # Output Validation
  output:
    schema: .claude/validation/schemas/agent-os/requirements-output.json
    required_files:
      - 'agent-os/specs/${spec_name}/requirements.md'
    min_file_size: 1000
    quality_threshold: 0.9

# Prerequisites
prerequisites:
  - command: /agent-os/init-spec
    file_exists: 'agent-os/specs/${spec_name}/idea.md'
---
```

### In Command Implementation

```javascript
// 1. Validate input
const validation = await validateInput({
  spec_name: ARGUMENTS
}, '.claude/validation/schemas/common/spec-name.json')

if (!validation.valid) {
  throw new Error(validation.errors.join(', '))
}

// 2. Execute agent
const result = await Task({
  subagent: 'spec-shaper',
  context: {
    spec_name: ARGUMENTS,
    spec_path: `agent-os/specs/${ARGUMENTS}`,
  },
  validation: {
    required_outputs: ['requirements.md'],
    quality_threshold: 0.9
  }
})

// 3. Validate output
const outputValidation = await validateOutput(
  result,
  '.claude/validation/schemas/agent-os/requirements-output.json'
)

if (!outputValidation.valid) {
  throw new Error(outputValidation.errors.join(', '))
}
```

## Validation Reports

Commands generate validation reports in JSON format:

```json
{
  "command": "/agent-os/shape-spec",
  "timestamp": "2026-01-20T10:30:00Z",
  "validation": {
    "input": {
      "valid": true,
      "errors": []
    },
    "execution": {
      "valid": true,
      "steps_completed": 5,
      "steps_failed": 0
    },
    "output": {
      "valid": true,
      "quality_score": 0.95,
      "files_created": [
        "agent-os/specs/user-auth/requirements.md"
      ],
      "warnings": []
    }
  },
  "overall_status": "success"
}
```

## Best Practices

### 1. Always Validate Inputs First

Catch errors early before expensive agent operations.

### 2. Use Progressive Validation

Validate at each step, not just at the end.

### 3. Provide Helpful Error Messages

Include hints for recovery and next steps.

### 4. Set Realistic Thresholds

Quality thresholds should be achievable but meaningful.

### 5. Log All Validation Results

Create audit trail for debugging and improvement.

## Schema Versioning

Schemas use semantic versioning:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://mahoosuc.dev/schemas/requirements-output.json",
  "version": "1.0.0",
  "title": "Requirements Output Schema"
}
```

## Integration with Hooks

Validation hooks run automatically:

```yaml
# .claude/hooks/pre-command/validate-input.yaml
triggers:
  - event: PreToolUse
    tool: SlashCommand
    filter: '/agent-os/*'

validation:
  enabled: true
  schema_path: .claude/validation/schemas/
  block_on_failure: true
  log_results: true
```

## Performance Considerations

- **Schema caching**: Schemas are cached in memory after first load
- **Async validation**: Large file validations run asynchronously
- **Batch validation**: Multiple files validated in parallel
- **Timeout limits**: Validation has 30-second timeout per command

## Troubleshooting

### Validation Failing Unexpectedly?

1. Check schema file exists and is valid JSON
2. Verify file paths use correct variable interpolation
3. Check file permissions
4. Review validation logs in `.claude/validation/logs/`

### False Positives?

1. Adjust quality thresholds in command frontmatter
2. Update schema to be more permissive
3. Add custom validation logic in command implementation

### Performance Issues?

1. Reduce number of validation checks
2. Increase validation timeout
3. Use schema caching
4. Validate only critical files

## Migration Checklist

When migrating a command to use validation:

- [ ] Identify all inputs (arguments, flags, environment)
- [ ] Create/reference input validation schema
- [ ] Define required outputs (files, data, artifacts)
- [ ] Create/reference output validation schema
- [ ] Add validation config to command frontmatter
- [ ] Update command implementation to use validators
- [ ] Test with valid inputs
- [ ] Test with invalid inputs (error handling)
- [ ] Document validation requirements
- [ ] Update command documentation

## Future Enhancements

Planned for Phase 3:

- **Real-time validation**: Validate during execution, not just before/after
- **ML-based quality scoring**: Use AI to assess output quality
- **Auto-correction**: Automatically fix common validation errors
- **Validation dashboards**: Web UI for validation metrics
- **Smart thresholds**: Adaptive quality thresholds based on command history

---

**Last Updated**: 2026-01-20
**Maintained By**: Mahoosuc Operating System Team
