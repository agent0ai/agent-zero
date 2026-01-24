---
description: Review /docs folder structure, ensure comprehensive knowledge base exists, and generate detailed roadmap if missing
argument-hint: "[--generate-roadmap] [--update-existing]"
allowed-tools: [Read, Glob, Write, Edit, Bash, AskUserQuestion]
---

# Documentation Review and Roadmap Generation

You are conducting a comprehensive review of the project's `/docs` folder to ensure it contains a well-organized knowledge base with a detailed roadmap for future development.

## Phase 1: Documentation Discovery

1. **Locate Documentation**:
   - Find the `/docs` folder (typically in project root or backend/)
   - List all existing documentation files
   - Check for standard docs: README.md, ROADMAP.md, ARCHITECTURE.md, CONTRIBUTING.md, CHANGELOG.md
   - Look for Architecture Decision Records (ADR) in `/docs/adr/`
   - Identify session notes, technical specs, and other documentation

2. **Analyze Current State**:
   - Categorize documentation by type:
     - Strategic (roadmap, vision, goals)
     - Technical (architecture, ADRs, API docs)
     - Process (contributing, workflows, development guides)
     - Historical (session notes, changelogs)
   - Identify gaps in documentation coverage
   - Check for outdated or incomplete documents

## Phase 2: Knowledge Base Assessment

Evaluate the documentation against best practices:

### Required Documentation Components

1. **Strategic Layer**:
   - [ ] ROADMAP.md - Detailed future plans with timelines
   - [ ] VISION.md - Long-term product vision
   - [ ] GOALS.md - Quarterly/annual objectives

2. **Technical Layer**:
   - [ ] ARCHITECTURE.md - System architecture overview
   - [ ] API.md - API documentation
   - [ ] DATABASE.md - Database schema and design
   - [ ] ADRs - Architecture Decision Records

3. **Process Layer**:
   - [ ] CONTRIBUTING.md - Contribution guidelines
   - [ ] DEVELOPMENT.md - Local development setup
   - [ ] TESTING.md - Testing strategies
   - [ ] DEPLOYMENT.md - Deployment procedures

4. **Historical Layer**:
   - [ ] CHANGELOG.md - Version history
   - [ ] Session notes - Development session summaries

### Quality Criteria

- **Completeness**: All major areas covered
- **Accuracy**: Up-to-date with current state
- **Clarity**: Well-structured and easy to navigate
- **Actionability**: Clear next steps and priorities

## Phase 3: Roadmap Generation (if missing or incomplete)

If ROADMAP.md is missing or insufficient, generate a comprehensive roadmap:

### Roadmap Structure

```markdown
# Project Roadmap

## Vision Statement
[Long-term vision for the project]

## Current State (As of [DATE])
- **Version**: [current version]
- **Maturity**: [alpha/beta/production]
- **Key Metrics**: [test pass rate, coverage, performance]
- **Recent Achievements**: [completed milestones]

## Immediate Priorities (Next 2-4 Weeks)
### High Priority
1. [Priority 1] - [Why it matters] - [Expected completion]
2. [Priority 2] - [Why it matters] - [Expected completion]

### Medium Priority
1. [Item] - [Rationale]
2. [Item] - [Rationale]

### Low Priority / Technical Debt
1. [Item] - [Can be deferred because...]

## Short-Term Goals (1-3 Months)
### Feature Development
- [Feature 1]: [Description] - [Value proposition]
- [Feature 2]: [Description] - [Value proposition]

### Technical Improvements
- [Improvement 1]: [Description] - [Impact]
- [Improvement 2]: [Description] - [Impact]

### Quality & Testing
- Target: [X%] test coverage
- [Specific testing improvements]

## Mid-Term Goals (3-6 Months)
### Major Features
- [Epic 1]: [Description] - [Strategic value]
- [Epic 2]: [Description] - [Strategic value]

### Platform Enhancements
- [Enhancement 1]
- [Enhancement 2]

### Performance & Scalability
- [Goal 1]: [Metric target]
- [Goal 2]: [Metric target]

## Long-Term Vision (6-12 Months)
### Strategic Initiatives
- [Initiative 1]: [Description and impact]
- [Initiative 2]: [Description and impact]

### Technology Evolution
- [Technology upgrade or migration]
- [New capabilities to add]

### Ecosystem Growth
- [Integration plans]
- [Partnership opportunities]

## Dependencies & Blockers
### External Dependencies
- [Dependency 1]: [Status] - [Mitigation plan]
- [Dependency 2]: [Status] - [Mitigation plan]

### Current Blockers
- [Blocker 1]: [Impact] - [Resolution plan]
- [Blocker 2]: [Impact] - [Resolution plan]

## Success Metrics
### Key Performance Indicators
- [KPI 1]: Current [X], Target [Y]
- [KPI 2]: Current [X], Target [Y]

### Milestone Tracking
- [Milestone 1]: [Target date] - [Status]
- [Milestone 2]: [Target date] - [Status]

## Risk Management
### Technical Risks
- [Risk 1]: [Likelihood] - [Impact] - [Mitigation]
- [Risk 2]: [Likelihood] - [Impact] - [Mitigation]

### Resource Risks
- [Risk 1]: [Description] - [Contingency plan]

## Decision Log
### Recent Decisions
- [DATE]: [Decision made] - [Rationale] - [ADR reference if applicable]

### Pending Decisions
- [Decision needed] - [Deadline] - [Decision makers]

## Archive
### Completed Milestones
- [Milestone]: [Completion date] - [Outcome]

### Deprecated Features
- [Feature]: [Deprecation date] - [Reason]
```

## Phase 4: Interactive Roadmap Generation with User

If generating a new roadmap, work collaboratively with the user:

### Step 1: Gather Context

Ask the user:

1. What are the most important features to build next?
2. What pain points need to be addressed urgently?
3. What's the current test pass rate and coverage goals?
4. What technical debt is most critical?
5. What are the 6-12 month strategic goals?

### Step 2: Analyze Existing Documentation

Extract information from:

- Session notes (recent work completed)
- IMPROVEMENTS_SUMMARY.md (known issues and priorities)
- Test results (failing tests, coverage gaps)
- ADRs (architectural decisions and their implications)
- CHANGELOG (recent changes and patterns)

### Step 3: Generate Draft Roadmap

Create a comprehensive roadmap based on:

- User input from Step 1
- Analysis from Step 2
- Best practices and realistic timelines
- Dependencies and blockers identified

### Step 4: User Review and Refinement

Present the draft roadmap and ask:

1. Are the priorities correct?
2. Are the timelines realistic?
3. What's missing or should be added?
4. What should be removed or deprioritized?

### Step 5: Finalize and Integrate

- Save the approved roadmap to `/docs/ROADMAP.md`
- Update related documentation (README.md links, CONTRIBUTING.md references)
- Create an ADR if major strategic decisions were made
- Add roadmap review to recurring process (monthly updates)

## Phase 5: Documentation Organization

Ensure the `/docs` folder is well-organized:

```
docs/
├── README.md                 # Documentation index
├── ROADMAP.md               # This roadmap
├── ARCHITECTURE.md          # System architecture
├── CONTRIBUTING.md          # Contribution guide
├── CHANGELOG.md             # Version history
├── adr/                     # Architecture Decision Records
│   ├── INDEX.md
│   ├── ADR-001-*.md
│   └── ADR-002-*.md
├── guides/                  # User and developer guides
│   ├── getting-started.md
│   ├── development.md
│   └── deployment.md
├── api/                     # API documentation
│   ├── endpoints.md
│   └── authentication.md
├── sessions/                # Development session notes
│   ├── session10.md
│   └── session11.md
└── archive/                 # Deprecated documentation
    └── old-architecture.md
```

## Phase 6: Maintenance Process

Establish a documentation maintenance process:

1. **Monthly Reviews**:
   - Review and update ROADMAP.md
   - Archive completed session notes
   - Update CHANGELOG.md

2. **Quarterly Assessments**:
   - Full documentation audit
   - Identify and fill gaps
   - Update strategic documents

3. **On-Demand Updates**:
   - Create ADR for significant architectural decisions
   - Update API docs when endpoints change
   - Document major features when completed

## Execution Steps

1. Run `find` to locate all documentation files
2. Read and analyze each document
3. Generate documentation coverage report
4. If ROADMAP.md is missing or incomplete:
   - Ask user questions about priorities
   - Analyze session notes and improvements
   - Generate comprehensive roadmap draft
   - Review with user
   - Finalize and save
5. Create documentation index (docs/README.md)
6. Suggest documentation maintenance schedule

## Success Criteria

✅ All required documentation categories have at least one document
✅ ROADMAP.md exists and is comprehensive (covers immediate, short-term, mid-term, long-term)
✅ Documentation is organized and easy to navigate
✅ Gaps identified and prioritized for filling
✅ Maintenance process established

## Output Format

Provide:

1. Documentation coverage report (% complete by category)
2. List of missing or incomplete documents
3. Generated roadmap (if applicable)
4. Recommended next steps for documentation improvement
5. Maintenance schedule proposal
