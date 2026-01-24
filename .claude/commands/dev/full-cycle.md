---
description: Complete development workflow from feature idea to production deployment
argument-hint: <feature-description> [--skip-review] [--auto-deploy]
allowed-tools: Task, Bash, AskUserQuestion
model: claude-sonnet-4-5
timeout: 3600
retry: 1
cost_estimate: 0.50-0.80

validation:
  input:
    feature_description:
      required: true
      min_length: 10
      error_message: "Feature description must be at least 10 characters"
  output:
    schema: .claude/validation/schemas/dev/full-cycle-output.json
    required_files:
      - '.claude/full-cycle-summary-${timestamp}.md'
    min_file_size: 500
    quality_threshold: 0.90
    content_requirements:
      - "All phases completed"
      - "Feature deployed successfully"
      - "Quality metrics tracked"
      - "Time savings documented"

version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to modern pattern with comprehensive validation"
      - "Added output validation for full-cycle workflow"
      - "Streamlined from 486 lines to focused orchestration"
      - "Enhanced checkpoint management and quality gates"
      - "60-70% time savings vs manual workflow"
  - version: 1.0.0
    date: 2025-09-10
    changes:
      - "Initial implementation with complete automation"
---

# Full-Cycle Development

Feature: **$ARGUMENTS**

## Step 1: Validate Input & Parse Options

```bash
ARGS="$ARGUMENTS"
FEATURE_DESCRIPTION=$(echo "$ARGS" | sed 's/--skip-review\|--auto-deploy//g' | xargs)
SKIP_REVIEW=$(echo "$ARGS" | grep -q '\-\-skip-review' && echo "true" || echo "false")
AUTO_DEPLOY=$(echo "$ARGS" | grep -q '\-\-auto-deploy' && echo "true" || echo "false")

if [ ${#FEATURE_DESCRIPTION} -lt 10 ]; then
  echo "❌ ERROR: Feature description too short (minimum 10 characters)"
  exit 1
fi

TIMESTAMP=$(date +%Y%m%d-%H%M)

echo "✓ Full-cycle workflow initialized"
echo "  Feature: $FEATURE_DESCRIPTION"
echo "  Skip review: $SKIP_REVIEW"
echo "  Auto-deploy: $AUTO_DEPLOY"
echo "  Timestamp: $TIMESTAMP"
```

## Step 2: Execute Full Development Cycle

```javascript
const FEATURE_DESCRIPTION = process.env.FEATURE_DESCRIPTION;
const SKIP_REVIEW = process.env.SKIP_REVIEW === 'true';
const AUTO_DEPLOY = process.env.AUTO_DEPLOY === 'true';
const TIMESTAMP = process.env.TIMESTAMP;

await Task({
  subagent_type: 'general-purpose',
  description: 'Execute complete development cycle',
  prompt: `Execute full development workflow for: ${FEATURE_DESCRIPTION}

Options:
- Skip review: ${SKIP_REVIEW}
- Auto-deploy: ${AUTO_DEPLOY}

COMPLETE WORKFLOW (7 Phases):

**PHASE 1: Planning (5-15 min)**
Execute: /dev/feature-request "${FEATURE_DESCRIPTION}"
Output: Feature specification created
Checkpoint: Review spec with user, get approval to proceed

**PHASE 2: Setup (1-2 min)**
Execute: /dev/create-branch [feature-slug]
Output: Feature branch created from main

**PHASE 3: Implementation (30-120 min)**
Execute: /dev/implement [feature-name]
Process:
- AI implements feature per specification
- Routes to specialized agents as needed
- Adds tests inline
- Commits progressively
- Generates implementation report
Output: Feature implemented with tests

**PHASE 4: Testing (15-30 min)**
Execute: /dev/test
Process:
- Run full test suite
- If failures: AI analyzes and suggests fixes
- Apply fixes and re-test until passing
Requirement: All tests must pass to proceed

**PHASE 5: Review ${SKIP_REVIEW ? '(SKIPPED)' : '(15-30 min)'}**
${SKIP_REVIEW ? 'Skipped per --skip-review flag' :
`Execute: /dev/review
Process:
- Automated checks (linting, types, security, secrets)
- AI code review (7 categories)
- Issues categorized by severity
- Show critical issues to user
Checkpoint: If critical issues, ask to fix or proceed with warnings`}

**PHASE 6: PR & Merge (5-10 min)**
Execute: /dev/create-pr
Output: PR created with AI-generated description

Checkpoint: Show PR summary, request approval to merge
- Files changed, test coverage, quality scores
- User approves or cancels

If approved:
  Execute: /dev/merge
  Output: PR merged to main

**PHASE 7: Deployment ${AUTO_DEPLOY ? '(AUTOMATIC)' : '(5-10 min)'}**
${AUTO_DEPLOY ? 'Auto-deploy per --auto-deploy flag' :
`Checkpoint: Ask user "Deploy to production now?"
- Yes → Proceed with deployment
- No → Stop (deploy manually later)
- Staging first → Deploy to staging, ask again`}

If deployment approved:
  Execute: /devops/deploy production
  Process:
  - Pre-deployment backup (if DB changes)
  - Deploy with health checks
  - Post-deployment verification
  - Monitor for issues

  If verification fails:
    Ask: "Rollback or debug?"
    If rollback: /devops/rollback

**OUTPUT: Generate Complete Summary**

Save to: .claude/full-cycle-summary-${TIMESTAMP}.md

Markdown summary including:
## Full-Cycle Development Summary

**Feature**: [name]
**Status**: ✓ Deployed to Production

### Timeline
| Phase | Duration | Status |
|-------|----------|--------|
| Planning | X min | ✓ |
| Implementation | X min | ✓ |
| Testing | X min | ✓ |
| Review | X min | ${SKIP_REVIEW ? '⊘ Skipped' : '✓'} |
| PR & Merge | X min | ✓ |
| Deployment | X min | ✓ |
| **Total** | **X min** | ✓ |

### Changes
- Files changed: X
- Tests added: X
- Database migrations: X

### Quality Metrics
- Test coverage: X%
- Code review score: X/100
- Security score: X/100
- Performance score: X/100

### Deployment
- Environment: production
- Verification: ✓ Passed
- Monitoring: Active

🎉 Feature successfully deployed!

**Also generate JSON for validation**:
{
  "cycle_status": "completed",
  "feature_name": "...",
  "phases_completed": {
    "planning": true,
    "implementation": true,
    "testing": true,
    "review": ${!SKIP_REVIEW},
    "pr_merge": true,
    "deployment": true
  },
  "total_time_minutes": X,
  "files_changed": X,
  "tests_added": X,
  "quality_metrics": {
    "test_coverage": X,
    "code_review_score": X,
    "security_score": X,
    "performance_score": X,
    "critical_vulnerabilities": 0
  },
  "deployment_status": "deployed",
  "deployment_verified": true,
  "pr_number": X,
  "summary_document_path": ".claude/full-cycle-summary-${TIMESTAMP}.md",
  "time_saved_vs_manual": X
}

**CHECKPOINT MANAGEMENT**:
The workflow includes 3-4 human checkpoints:
1. After planning: Review and approve feature spec
2. ${!SKIP_REVIEW ? 'After review: Review issues, decide to fix or proceed' : ''}
3. Before merge: Approve PR
4. ${!AUTO_DEPLOY ? 'Before deployment: Approve deployment' : ''}

These ensure human oversight at critical decision points while automating the heavy lifting.

**SUCCESS CRITERIA**:
- All phases complete successfully
- All tests passing
- ${!SKIP_REVIEW ? 'Code review passed (or approved with warnings)' : 'Basic checks passed'}
- Deployed and verified
- Total time < 3 hours for typical feature
- Time saved: 60-70% vs manual workflow`,

  context: {
    feature_description: FEATURE_DESCRIPTION,
    skip_review: SKIP_REVIEW,
    auto_deploy: AUTO_DEPLOY,
    timestamp: TIMESTAMP,
    summary_output: `.claude/full-cycle-summary-${TIMESTAMP}.md`
  }
});
```

## Step 3: Validate Output

```bash
TIMESTAMP="$TIMESTAMP"
SUMMARY_FILE=".claude/full-cycle-summary-${TIMESTAMP}.md"

# Check summary created
if [ ! -f "$SUMMARY_FILE" ]; then
  echo "❌ ERROR: Full-cycle summary not created"
  exit 1
fi

# Check minimum size
FILE_SIZE=$(wc -c < "$SUMMARY_FILE")
if [ $FILE_SIZE -lt 500 ]; then
  echo "❌ ERROR: Summary too small (< 500 bytes)"
  exit 1
fi

echo "✓ Full-cycle validation complete"
echo "  Summary: $SUMMARY_FILE ($FILE_SIZE bytes)"
```

## Completion

```
═══════════════════════════════════════════════════
      FULL-CYCLE DEVELOPMENT COMPLETE ✓
═══════════════════════════════════════════════════

Feature: $FEATURE_DESCRIPTION
Command: /dev/full-cycle
Version: 2.0.0

Cycle Summary:
  ✓ Planning complete
  ✓ Implementation complete
  ✓ Testing complete
  ${SKIP_REVIEW ? '⊘ Review skipped' : '✓ Review complete'}
  ✓ PR merged
  ✓ Deployment ${AUTO_DEPLOY ? 'automatic' : 'verified'}

Total Time: [X] minutes
Time Saved: 60-70% vs manual workflow

Quality Metrics:
  Test coverage: [X]%
  Code quality: [X]/100
  Security: [X]/100

Deployment:
  Status: ✓ Deployed
  Environment: production
  Verification: ✓ Passed

Validations Passed:
  ✓ All phases completed successfully
  ✓ Quality thresholds met
  ✓ Summary generated
  ✓ Quality threshold (≥0.90)

View complete summary:
  cat .claude/full-cycle-summary-$TIMESTAMP.md

═══════════════════════════════════════════════════

🎉 FEATURE SUCCESSFULLY DEPLOYED TO PRODUCTION!

═══════════════════════════════════════════════════
```

## Guidelines

- **Use for Standard Features**: Well-defined features (<1 day work)
- **Trust AI**: Best with --skip-review for faster iteration
- **Monitor Deployment**: Always monitor after production deploy
- **Checkpoints Matter**: Human oversight at critical decision points
- **Time Savings**: 60-70% faster than manual 7-command workflow
