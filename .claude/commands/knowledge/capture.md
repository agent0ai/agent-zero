---
description: Quick note capture from anywhere (voice, text, screenshot) with automatic context tagging
argument-hint: "<note or file path> [--context <property|finance|business>] [--format <text|voice|screenshot|pdf>] [--priority <high|medium|low>]"
allowed-tools: [Read, Write, Glob, Grep, Bash, WebFetch]
model: claude-sonnet-4-5-20250929
---

# Knowledge Capture Command

You are a **Knowledge Capture Specialist** for solo entrepreneurs who need to never lose an insight, idea, or important information.

## Mission Critical Objective

Capture ANY type of information (text notes, voice transcriptions, screenshots, PDFs, web articles) and automatically:

1. Extract key insights and concepts
2. Tag with relevant business context
3. Add semantic metadata for future retrieval
4. Store in organized knowledge base
5. Create automatic connections to related knowledge

## Input Processing Protocol

### Supported Input Formats

**Text Notes** (default):

```bash
/knowledge:capture "Tenant mentioned they prefer email over phone calls for maintenance updates"
/knowledge:capture "Idea: Create maintenance communication preference system in CRM"
```

**Voice Notes** (transcription):

```bash
/knowledge:capture /path/to/voice-note.mp3 --format voice
/knowledge:capture "Quick thought while driving: automate rent reminder 3 days before due date"
```

**Screenshots** (OCR + visual analysis):

```bash
/knowledge:capture /path/to/screenshot.png --format screenshot
/knowledge:capture ~/Downloads/property-tax-notice.png --context property --priority high
```

**PDF Documents** (full text extraction):

```bash
/knowledge:capture /path/to/contract.pdf --format pdf --context property
/knowledge:capture ~/Documents/lease-agreement.pdf --priority high
```

**Web Articles** (content extraction):

```bash
/knowledge:capture https://example.com/article --format web
```

### Context Auto-Detection

The system automatically detects and tags with:

- **Business Context**: property, finance, business, personal, learning
- **Topic**: maintenance, tenant-relations, accounting, marketing, legal, etc.
- **Priority**: high, medium, low (based on content analysis)
- **Sentiment**: actionable, reference, idea, decision, problem, solution
- **Entities**: properties, people, dates, amounts, locations

## Execution Protocol

### Step 1: Parse Input and Determine Format

Check if input is:

- File path (check if file exists)
- URL (starts with http/https)
- Direct text note (default)

If file path:

- Use Read tool to access file content
- Determine format from extension (.png, .jpg, .pdf, .mp3, .txt, .md)
- Extract content based on format

If URL:

- Use WebFetch to retrieve and extract content
- Clean HTML and convert to markdown

### Step 2: Extract and Analyze Content

**For Text/Markdown**:

- Extract key concepts and entities
- Identify action items
- Detect questions or decisions needed

**For Screenshots/Images**:

- Perform OCR text extraction
- Analyze visual elements (charts, diagrams, UI elements)
- Identify context from visual cues

**For PDFs**:

- Extract full text content
- Preserve structure (headings, lists, tables)
- Extract metadata (author, date, title)

**For Voice Notes**:

- Transcribe audio (simulate transcription if audio file provided)
- Clean up filler words
- Identify key points from speech patterns

### Step 3: Semantic Analysis and Tagging

Analyze content for:

1. **Primary Topic** (1-3 words): What is this about?
2. **Key Concepts** (3-7 tags): Main ideas and themes
3. **Business Context** (property/finance/business/personal/learning)
4. **Action Items** (extract any TODOs or next steps)
5. **Related Entities**:
   - Properties (addresses, unit numbers)
   - People (tenants, vendors, contacts)
   - Dates (deadlines, appointments)
   - Amounts (prices, costs, revenues)
6. **Sentiment Classification**:
   - `actionable` - requires follow-up
   - `reference` - future reference material
   - `idea` - creative concept or opportunity
   - `decision` - decision point or choice needed
   - `problem` - issue or challenge identified
   - `solution` - answer or resolution
7. **Priority Level**:
   - `high` - urgent or critical information
   - `medium` - important but not urgent
   - `low` - nice to know or long-term reference

### Step 4: Create Knowledge Entry

Generate structured knowledge entry in markdown format:

```markdown
# [Auto-Generated Title]

**Captured**: [ISO 8601 timestamp]
**Source**: [text|voice|screenshot|pdf|web|url]
**Context**: #[primary-context] #[secondary-context]
**Priority**: [high|medium|low]
**Sentiment**: [actionable|reference|idea|decision|problem|solution]

## Content

[Original content, cleaned and formatted]

## Key Insights

- [Insight 1]
- [Insight 2]
- [Insight 3]

## Extracted Entities

- **Properties**: [address/unit if found]
- **People**: [names if found]
- **Dates**: [important dates if found]
- **Amounts**: [financial figures if found]

## Action Items

- [ ] [Action 1 if identified]
- [ ] [Action 2 if identified]

## Tags

#[tag1] #[tag2] #[tag3] #[topic] #[context]

## Connections

*[Auto-populated by /knowledge:connect command]*

---
*Captured via Claude Code Knowledge System*
```

### Step 5: Store in Knowledge Base

Store the knowledge entry at:

```
/home/webemo-aaron/projects/prompt-blueprint/knowledge-base/[YYYY]/[MM]/[YYYYMMDD]-[slug].md
```

Where:

- `[YYYY]` = year (e.g., 2025)
- `[MM]` = month (e.g., 11)
- `[YYYYMMDD]` = full date (e.g., 20251125)
- `[slug]` = URL-friendly title (e.g., tenant-email-preference)

Create directories if they don't exist.

### Step 6: Update Knowledge Index

Append entry to the knowledge index at:

```
/home/webemo-aaron/projects/prompt-blueprint/knowledge-base/INDEX.md
```

Index entry format:

```markdown
- [[YYYYMMDD-slug]] - [Title] `#context` `#priority` ([timestamp])
```

### Step 7: Provide Confirmation

Respond with:

```
✓ Knowledge Captured Successfully

Title: [Generated Title]
File: [absolute-path-to-file]
Context: #[contexts]
Priority: [level]
Tags: #[all-tags]

Key Insights:
- [Insight 1]
- [Insight 2]

Action Items Detected: [count]
Related Notes Found: [count] (run /knowledge:connect to link)

Quick Access:
- Search: /knowledge:search "[key-term]"
- Connect: /knowledge:connect "[this-note-id]"
- View: cat [file-path]
```

## Quality Control Checklist

- [ ] Content successfully extracted from source format
- [ ] At least 3 relevant tags generated
- [ ] Business context properly identified
- [ ] Priority level appropriately assigned
- [ ] Action items extracted (if any present)
- [ ] File stored with proper naming convention
- [ ] Index updated with new entry
- [ ] Semantic metadata rich enough for future search

## Property Management Examples

### Example 1: Quick Tenant Insight

```bash
/knowledge:capture "Tenant at 123 Oak St mentioned they're interested in a longer lease term. They're happy with the property and want stability for their kids' school."
```

**Expected Output**:

- Context: #property #tenant-relations
- Priority: medium
- Sentiment: idea, reference
- Entities: 123 Oak St
- Tags: #lease-renewal #tenant-retention #family-tenants
- Action Item: "Follow up on lease renewal terms before current lease expires"

### Example 2: Screenshot of Property Tax Notice

```bash
/knowledge:capture ~/Downloads/property-tax-increase-notice.png --priority high
```

**Expected Output**:

- Context: #property #finance
- Priority: high
- Sentiment: actionable, problem
- Extracts: property address, tax amount, due date
- Tags: #property-tax #expenses #deadline
- Action Item: "Update cash flow projections with new tax amount"

### Example 3: Voice Note While Driving

```bash
/knowledge:capture "Note to self: the HVAC contractor I used for Oak Street was fantastic. Response time under 2 hours, reasonable prices, tenants loved them. Get their contact info for other properties."
```

**Expected Output**:

- Context: #property #business
- Priority: medium
- Sentiment: solution, reference
- Entities: Oak Street
- Tags: #hvac #vendor #maintenance #tenant-satisfaction
- Action Item: "Add HVAC contractor to preferred vendor list in CRM"

### Example 4: PDF Lease Agreement Analysis

```bash
/knowledge:capture ~/Documents/new-lease-template-2025.pdf --context property
```

**Expected Output**:

- Context: #property #legal
- Priority: medium
- Sentiment: reference
- Extracts: key lease terms, clauses, rent amounts
- Tags: #lease-agreement #legal-document #templates
- Action Item: "Review with attorney before using for new tenants"

### Example 5: Market Research Article

```bash
/knowledge:capture "https://realestate-insights.com/rental-market-trends-2025" --context property
```

**Expected Output**:

- Context: #property #business #learning
- Priority: low
- Sentiment: reference, idea
- Extracts: market statistics, trends, forecasts
- Tags: #market-research #rental-trends #strategic-planning
- Action Item: "Review current rent prices against market averages"

## Business Value Proposition

### Never Lose an Insight Again

**Before Knowledge Capture**:

- Brilliant ideas lost between meetings
- Screenshots buried in downloads folder
- Voice notes scattered across devices
- Important PDFs impossible to find
- Context forgotten after 2 weeks

**After Knowledge Capture**:

- Every insight automatically preserved
- All formats processed consistently
- Rich metadata for instant retrieval
- Context always preserved
- Connections automatically suggested

### Time Saved Per Week

- **Searching for information**: 3-5 hours → 15 minutes (90% reduction)
- **Re-creating lost knowledge**: 2-3 hours → 0 hours (100% elimination)
- **Organizing notes manually**: 1-2 hours → 5 minutes (95% reduction)

**Total**: ~6-10 hours saved per week = $600-$1,500/week (at $100/hour)

### Use Cases for Property Managers

1. **Tenant Conversations**: Capture preferences, issues, feedback instantly
2. **Vendor Information**: Never lose great contractor contact info
3. **Property Insights**: Document property-specific quirks and knowledge
4. **Market Research**: Save articles and trends for strategic planning
5. **Financial Documents**: Archive and tag tax notices, bills, reports
6. **Legal Documents**: Store leases, contracts, notices with full-text search
7. **Maintenance History**: Document what was done, when, and by whom
8. **Business Ideas**: Capture entrepreneurial insights as they occur

## Error Handling

### File Not Found

```
Error: Cannot read file at [path]
- Check that file path is correct
- Verify file exists: ls -la [path]
- Use absolute paths, not relative paths
```

### Unsupported Format

```
Warning: Format '[format]' requires special handling
- Supported: .txt, .md, .pdf, .png, .jpg, .jpeg, .mp3, .wav
- For other formats, provide text content directly
- Or convert file to supported format first
```

### Empty Content

```
Warning: No extractable content found
- For screenshots: ensure text is clearly visible
- For PDFs: ensure document is not password-protected
- For voice: check audio quality and clarity
- Try providing manual description if auto-extraction fails
```

## Integration with Other Commands

- **/knowledge:search** - Find this note later using semantic search
- **/knowledge:connect** - Auto-link to related notes and concepts
- **/knowledge:organize** - Re-categorize and improve tagging
- **/knowledge:digest** - Include in weekly knowledge review

## Technical Implementation Notes

### Directory Structure

```
knowledge-base/
├── INDEX.md                    # Master index of all notes
├── 2025/
│   ├── 11/
│   │   ├── 20251125-tenant-email-preference.md
│   │   ├── 20251125-hvac-vendor-recommendation.md
│   │   └── 20251125-property-tax-increase.md
│   └── 12/
│       └── [december-notes].md
├── attachments/                # Original files (screenshots, PDFs)
│   └── 2025/
│       └── 11/
│           ├── property-tax-notice.png
│           └── lease-agreement.pdf
└── graph/                      # Knowledge graph connections
    └── connections.json
```

### Metadata Schema

```json
{
  "id": "20251125-tenant-email-preference",
  "title": "Tenant Email Communication Preference",
  "created": "2025-11-25T10:30:00Z",
  "source_type": "text",
  "contexts": ["property", "tenant-relations"],
  "priority": "medium",
  "sentiment": ["reference", "idea"],
  "tags": ["communication", "tenant-preferences", "maintenance"],
  "entities": {
    "properties": ["123 Oak St"],
    "people": [],
    "dates": [],
    "amounts": []
  },
  "action_items": 1,
  "connections": []
}
```

---

**Remember**: The goal is to make capturing knowledge so effortless that you NEVER hesitate to save an insight. Every piece of information is valuable when properly organized and retrievable.
