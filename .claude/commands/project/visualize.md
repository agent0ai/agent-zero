---
description: "Analyze project and generate comprehensive Mermaid diagrams across 7 categories"
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
  - Task
  - AskUserQuestion
argument-hint: "[project-path] [--focus <category>] [--level <high|medium|detail>]"
---

# /project:visualize - Project Analysis & Diagram Generation

Generate comprehensive architecture diagrams for any project by analyzing its structure and codebase.

## Quick Start

**Basic usage:**

```bash
/project:visualize
```

**Focus on specific category:**

```bash
/project:visualize --focus architecture
/project:visualize --focus data
/project:visualize --focus api
```

**Specify detail level:**

```bash
/project:visualize --level high       # C4 Context only
/project:visualize --level medium     # Default - balanced detail
/project:visualize --level detail     # Maximum detail (all diagrams)
```

**Analyze specific project:**

```bash
/project:visualize /path/to/project
```

---

## System Overview

This command implements a **4-phase workflow** that automatically detects your project type, recommends diagrams, generates them using the mermaid-architect agent, and organizes results.

### What It Does

1. **Phase 1:** Auto-detect project type and technology stack
2. **Phase 2:** Suggest appropriate diagrams (with user approval)
3. **Phase 3:** Generate diagrams using AI agent
4. **Phase 4:** Organize results and create DIAGRAMS.md

### Output Structure

```
docs/diagrams/
├── architecture/
│   ├── 01-c4-context.mmd
│   ├── 02-c4-container.mmd
│   └── 03-c4-component.mmd
├── data/
│   ├── 01-database-erd.mmd
│   └── 02-data-flow.mmd
├── api/
│   ├── 01-auth-sequence.mmd
│   ├── 02-payment-sequence.mmd
│   └── 03-api-map.mmd
├── ui/
│   ├── 01-component-tree.mmd
│   └── 02-page-flow.mmd
└── DIAGRAMS.md
```

---

## Implementation

### Phase 1: Project Analysis & Auto-Detection

**Step 1.1: Read Project Root**

```bash
ls -la [project-path] | head -20
```

**Step 1.2: Detect Frontend Framework**

- Check for package.json with react/vue/angular
- Look for next.config.js, nuxt.config.js
- Scan src/pages, src/components directories

**Step 1.3: Detect Backend Framework**

- Look for server.js, main.py, app.rb
- Detect Express, FastAPI, Django, Rails
- Find API routes in routes/, routers/ directories

**Step 1.4: Detect Database & ORM**

- Check for prisma/schema.prisma
- Look for migrations/ folders
- Detect ORM usage (TypeORM, Sequelize, etc.)

**Step 1.5: Detect Deployment**

- Look for Dockerfile (containerization)
- Check .github/workflows/ (GitHub Actions)
- Scan for terraform/, k8s/ (Infrastructure as Code)

**Detection Output Example:**

```
Project Analysis Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project Type: Full-Stack Next.js Application
Project Size: Medium (2,847 files, 125K LOC)

Technology Stack:
  • Frontend: Next.js 14 + React + TypeScript
  • Backend: Next.js API Routes + Express
  • Database: PostgreSQL (Prisma ORM)
  • Deployment: Vercel
  • Authentication: NextAuth.js

Detected Patterns:
  ✓ API endpoints (23 routes detected)
  ✓ Database schema (8 tables found)
  ✓ Authentication (NextAuth config found)
  ✓ Webhooks (stripe-webhook endpoint)
  ✗ Event bus (not detected)
  ✗ Message queue (not detected)
```

### Phase 2: Diagram Suggestion & Approval

**Step 2.1: Generate Recommendations**

```
RECOMMENDED DIAGRAMS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Architecture (Required):
  [✓] C4 Context      - System in enterprise context
  [✓] C4 Container    - Technology and services
  [ ] C4 Component    - Internal structure (optional)

Data (Detected Database):
  [✓] Database ERD    - Entity relationships (8 tables)
  [ ] Data Flow       - Data transformation (optional)

API (Detected 23 endpoints):
  [✓] Auth Sequence   - Authentication flow
  [✓] Payment Seq     - Payment processing (Stripe)
  [✓] API Map         - All endpoints categorized

UI (Detected React):
  [✓] Component Tree  - React component hierarchy
  [✓] Page Flow       - Routing and navigation
```

**Step 2.2: Prompt User**

```
Proceed with recommended diagrams? (7 total)
[1] Generate all recommended (default)
[2] Focus on specific category
[3] Customize selection
[4] Cancel
```

**Checkpoint 1: Diagram Selection**

- User selects which diagrams to generate
- Can focus on single category or customize
- Can specify detail level

### Phase 3: Diagram Generation

**For Each Selected Diagram:**

1. Gather relevant context from project
2. Route to mermaid-architect agent via Task tool
3. Collect generated Mermaid diagram code
4. Validate syntax and render correctness
5. Store in appropriate directory

**Progress Indicator:**

```
Generating Diagrams... [████████░░] 7/9

✓ C4 Context (2 min 15s)
✓ C4 Container (3 min 42s)
✓ Database ERD (5 min 18s)
⏳ API Map (generating...)
⬜ Component Tree
```

**Checkpoint 2: Diagram Review**

```
Review generated diagrams:
[1] All diagrams look good (proceed)
[2] Refine specific diagram
[3] Regenerate all
```

### Phase 4: Documentation & Organization

**Step 4.1: Create Directory Structure**

```
docs/diagrams/
├── architecture/
├── data/
├── api/
├── ui/
└── DIAGRAMS.md
```

**Step 4.2: Save All Diagrams**

- Each diagram → numbered .mmd file
- Organized by category
- Clear naming convention

**Step 4.3: Generate DIAGRAMS.md**

Consolidated view of all diagrams with:

- Diagram categories (Architecture, Data, API, UI)
- Mermaid code blocks for each diagram
- Brief descriptions
- Usage instructions
- Update procedures

**Checkpoint 3: Final Review**

```
Documentation complete!
✓ 7 diagrams generated
✓ docs/diagrams/ created
✓ DIAGRAMS.md consolidated

Next steps:
[1] View diagrams
[2] Commit to repository
[3] Share with team
```

---

## Diagram Categories

### Architecture (C4 Model)

- **C4 Context:** System in enterprise context
- **C4 Container:** Major technology choices
- **C4 Component:** Internal structure detail

### Data & Database

- **Entity-Relationship Diagram:** Database schema
- **Data Flow Diagram:** Data movement patterns

### API & Integration

- **Authentication Sequence:** Login flows
- **Payment Processing:** Payment gateway flows
- **API Map:** All endpoints categorized

### Frontend & UI

- **Component Tree:** React/Vue hierarchy
- **Page Flow:** Routing and navigation

### Events & Async

- **Event Flow:** Message queue visualization
- **Webhook Map:** External callbacks

### AI & Agents

- **Agent Routing:** Request distribution
- **Agent Coordination:** Multi-agent communication

### Deployment & DevOps

- **Deployment Diagram:** Infrastructure
- **CI/CD Pipeline:** Build and deployment

---

## Advanced Usage

### Focus on Specific Category

```bash
/project:visualize --focus architecture
```

Generates only architecture diagrams.

### Specify Detail Level

```bash
/project:visualize --level high
```

Options:

- **high:** C4 Context only
- **medium:** Context + Container (default)
- **detail:** All diagrams with maximum depth

### Update Existing Diagrams

```bash
/project:visualize --update
```

Regenerates without user interaction (good for CI/CD).

### Custom Project Path

```bash
/project:visualize /path/to/project
```

Analyzes different project directory.

---

## Success Criteria

**Project Detection:**

- ✅ Correctly identifies project type
- ✅ Finds all major technologies
- ✅ Detects patterns (auth, payments, etc.)

**Diagram Generation:**

- ✅ Valid Mermaid syntax
- ✅ Clear and readable (≤9 elements)
- ✅ Matches architecture accurately
- ✅ Professional quality

**Documentation:**

- ✅ DIAGRAMS.md includes all diagrams
- ✅ Clear descriptions provided
- ✅ Usage instructions included
- ✅ Easy to maintain and update

---

## Troubleshooting

### No Diagrams Generated

- Verify project path is correct
- Ensure project has recognizable structure
- Try with --level high for basic diagrams

### Diagram Looks Wrong

- Review Phase 1 architecture analysis
- Use --focus to regenerate specific diagram
- Manually edit the .mmd file if needed

### Missing Specific Diagram Type

- Use --level detail to generate more diagrams
- Verify required technologies are detected
- Manually create using mermaid-architect agent

---

## Command Workflow

```
START
  ↓
Phase 1: Detect Project (5-10 min)
  • Analyze structure
  • Detect frameworks
  • Find patterns
  ↓
Phase 2: Recommend Diagrams (1 min)
  [CHECKPOINT 1]
  ↓
Phase 3: Generate Diagrams (10-20 min)
  • Route to mermaid-architect agent
  • Collect outputs
  • Validate
  [CHECKPOINT 2]
  ↓
Phase 4: Organize & Document (5 min)
  • Create structure
  • Save diagrams
  • Generate DIAGRAMS.md
  [CHECKPOINT 3]
  ↓
END
```

---

## Notes

- **First Run:** 20-35 minutes total
- **Updates:** 5-10 minutes
- **Works Best:** Projects ≤ 500K LOC
- **Storage:** Minimal (1-5MB for all diagrams)

Keep diagrams updated by running:

```bash
/project:visualize --update
```

Whenever architecture changes significantly.
