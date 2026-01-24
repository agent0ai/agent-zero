---
description: Organize research materials into structured knowledge base
argument-hint: [--structure <topic|chronological|source|methodology>] [--tags] [--export <obsidian|notion|roam>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Write, Bash
---

# Research Organization Command

Transform scattered research materials into a structured, searchable knowledge management system.

## ROI: $35,000/year

- Save 20 hours/month on research organization (70% time reduction)
- Eliminate $12,000/year in knowledge management software costs
- Reduce time to find research materials by 85% with smart tagging
- Enable 3x faster literature review with structured organization
- Support multiple organization schemes (topic, chronological, methodology)
- Auto-link related research with bidirectional connections

## Key Benefits

- **Multi-Structure Support**: Organize by topic, chronology, source type, methodology, or custom taxonomy
- **Smart Tagging System**: Auto-tag research with keywords, concepts, authors, and methodologies
- **Bidirectional Linking**: Create wiki-style connections between related research materials
- **Full-Text Search**: Lightning-fast search across all notes, annotations, and source documents
- **Hierarchical Organization**: Multi-level folders and categories with inheritance
- **Visual Knowledge Graphs**: Interactive visualizations of research connections
- **Export Compatibility**: Seamlessly export to Obsidian, Notion, Roam Research, Zettelkasten
- **Metadata Preservation**: Maintain citation information, dates, authors, and custom fields

## Implementation Steps

### Step 1: Research Material Inventory and Assessment

Identify and catalog all research materials to be organized:

Source types to inventory:

- **Academic Papers**: PDFs, journal articles, conference proceedings
- **Books**: Full books, chapters, excerpts, eBooks
- **Websites**: Bookmarks, saved pages, web archives
- **Notes**: Personal annotations, highlights, marginalia
- **Data**: Datasets, spreadsheets, analysis results
- **Media**: Videos, podcasts, webinars, lectures
- **Documents**: Reports, whitepapers, technical docs
- **References**: Citations, bibliographies, reading lists

Extract metadata from each source:

- Title, author(s), publication date
- Source type and format
- Subject area and keywords
- Current location (file path, URL, physical)
- Related sources and connections
- Status (to-read, in-progress, completed, referenced)
- Quality rating and relevance score
- Creation date and last accessed

Assess organization needs:

- Total volume of materials (number of sources)
- Primary research topics and themes
- Research methodology (systematic review, meta-analysis, exploratory)
- Collaboration requirements (solo vs team)
- Access patterns (how often each source is referenced)
- Integration requirements (existing tools, workflows)

Generate inventory report:

- Source count by type and status
- Coverage analysis (topics well-covered vs gaps)
- Duplication detection (same source in multiple formats)
- Orphaned materials (no connections to main research)
- Missing metadata fields
- Recommended organization structure

### Step 2: Define Organization Structure and Taxonomy

Design the optimal structure for research materials:

**Topic-Based Organization**:

```
Research Database/
├── Machine Learning/
│   ├── Supervised Learning/
│   │   ├── Neural Networks/
│   │   ├── Decision Trees/
│   │   └── Support Vector Machines/
│   ├── Unsupervised Learning/
│   │   ├── Clustering/
│   │   └── Dimensionality Reduction/
│   └── Reinforcement Learning/
├── Natural Language Processing/
│   ├── Language Models/
│   ├── Sentiment Analysis/
│   └── Machine Translation/
└── Computer Vision/
    ├── Object Detection/
    ├── Image Segmentation/
    └── Face Recognition/
```

**Chronological Organization**:

```
Research Timeline/
├── Historical (pre-2000)/
├── Foundational (2000-2010)/
├── Recent (2010-2020)/
├── Current (2020-2024)/
└── Emerging (2024+)/
```

**Methodology Organization**:

```
Research Methods/
├── Experimental Studies/
├── Observational Studies/
├── Meta-Analyses/
├── Systematic Reviews/
├── Case Studies/
└── Theoretical Papers/
```

**Source-Type Organization**:

```
By Source/
├── Journal Articles/
├── Conference Papers/
├── Books & Chapters/
├── Technical Reports/
├── Theses & Dissertations/
├── Patents/
└── Gray Literature/
```

**Custom Hybrid Structure**:
Combine multiple organization schemes:

- Primary structure: Topic hierarchy
- Secondary tags: Methodology, year, authors
- Cross-references: Related topics and sources
- Collections: Reading lists, literature reviews, projects

Define taxonomy standards:

- Naming conventions for folders and files
- Tag vocabulary (controlled vs free-form)
- Metadata schema (required vs optional fields)
- File naming patterns (author-year-title.pdf)
- Hierarchy depth limits (3-5 levels recommended)

### Step 3: Tagging System Design and Implementation

Create comprehensive tagging system for research discovery:

**Core Tag Categories**:

Research Topics:

- Primary subject area (broad field)
- Specific topics (narrow focus)
- Keywords from title and abstract
- Domain-specific terminology
- Related concepts and themes

Methodologies:

- Research design (experimental, observational, etc.)
- Data collection methods (survey, interview, sensor)
- Analysis techniques (statistical, qualitative, computational)
- Sample characteristics (size, population, setting)
- Limitations and constraints

Authors and Institutions:

- Author names (for tracking key researchers)
- Institutional affiliations
- Research groups and labs
- Collaborator networks
- Author expertise areas

Temporal Tags:

- Publication year and era
- Research period (data collection timeframe)
- Historical context
- Trend indicators (emerging, established, declining)

Quality Indicators:

- Peer review status (peer-reviewed, preprint, draft)
- Impact factor and citations
- Sample size and statistical power
- Methodological rigor
- Replication status (replicated, failed replication, original)

Custom Tags:

- Project-specific labels
- Reading status (to-read, reading, read, reference)
- Action items (needs-annotation, needs-citation, needs-review)
- Importance level (critical, important, supplementary)
- Application domains (clinical, industrial, educational)

**Tag Implementation Strategies**:

Auto-tagging from metadata:

- Extract keywords from titles and abstracts
- Parse author names and institutions
- Detect methodology keywords
- Identify publication years and venues
- Extract subject classifications (ACM, MeSH, JEL)

Manual curated tags:

- Add custom relevance tags
- Note personal insights and connections
- Mark key findings and contributions
- Label limitations and critiques
- Identify practical applications

Hierarchical tag structure:

- Parent tags: Broad categories
- Child tags: Specific subcategories
- Tag inheritance: Auto-apply parent tags
- Tag synonyms: Handle variations (ML, machine learning)

Tag validation and quality control:

- Check for misspellings and typos
- Identify rarely used tags (candidates for removal)
- Detect tag overlap and redundancy
- Suggest tag consolidation
- Maintain tag glossary

### Step 4: Bidirectional Linking and Connection Mapping

Create network of interconnected research materials:

**Link Types**:

Explicit links:

- [[Related Work]]: Direct references to other research
- [[Builds On]]: Papers that extend or build upon
- [[Contradicts]]: Conflicting findings or arguments
- [[Supports]]: Evidence supporting claims
- [[Critiques]]: Critical analysis of other work
- [[Methodology Similar]]: Similar research approaches
- [[Dataset Shared]]: Uses same or overlapping data

Implicit links (auto-detected):

- Shared authors
- Shared citations (cite same papers)
- Shared keywords and topics
- Similar abstracts (semantic similarity)
- Temporal proximity (published around same time)
- Venue correlation (same journals or conferences)

Contextual links:

- [[Background Reading]]: Foundational knowledge
- [[See Also]]: Related but not directly cited
- [[Example]]: Illustrative cases
- [[Application]]: Practical use cases
- [[Future Work]]: Suggested next steps
- [[Replication]]: Studies attempting to replicate

**Connection Mapping**:

Create knowledge graph structure:

```
Source A (Node)
├── cites: Source B, Source C
├── cited-by: Source D, Source E
├── similar-to: Source F
├── contradicts: Source G
└── extends: Source H
```

Graph analysis features:

- Identify hub papers (highly connected)
- Find bridge papers (connect different clusters)
- Detect research communities (densely connected groups)
- Trace citation lineage (citation chains)
- Discover missing connections (should cite but doesn't)

Bidirectional link maintenance:

- Auto-create backlinks when forward link created
- Update link graph when sources added/removed
- Validate link targets (check source still exists)
- Track broken links and orphaned sources
- Suggest new connections based on similarity

Visual representations:

- Network graph of all connections
- Citation flow diagrams
- Topic cluster maps
- Timeline visualization of research evolution
- Author collaboration networks

### Step 5: Hierarchical Folder Structure Creation

Build logical folder hierarchy for research organization:

**Folder Design Principles**:

Balanced hierarchy:

- Not too shallow (everything in root)
- Not too deep (6+ levels hard to navigate)
- Optimal depth: 3-4 levels
- Each folder should have 3-10 subfolders
- Keep similar items at similar hierarchy levels

Mutually exclusive categories:

- Each source belongs to one primary folder
- Use tags for cross-cutting categorizations
- Avoid ambiguous folder names
- Clear naming conventions
- Prevent overlap between sibling folders

Scalable structure:

- Room for growth in each category
- Easy to add new subcategories
- Flexible enough for emerging topics
- Future-proof naming
- Regular structure review and refactoring

**Folder Metadata**:

Each folder contains:

- README.md with folder purpose and scope
- Index of contained sources
- Subtopic definitions
- Related folder cross-references
- Folder-specific tags and keywords
- Curation guidelines

Folder-level operations:

- Export entire folder as collection
- Generate folder-specific bibliography
- Create folder summary/overview
- Track folder growth over time
- Monitor folder health (stale content, orphans)

### Step 6: Note-Taking and Annotation System

Integrate personal notes with research materials:

**Note Types**:

Literature notes:

- Summary of main arguments
- Key findings and results
- Methodology overview
- Strengths and weaknesses
- Relevance to own research
- Direct quotes with page numbers

Permanent notes (Zettelkasten-style):

- Atomic notes (one concept per note)
- Written in own words
- Standalone and evergreen
- Linked to source materials
- Connected to related concepts
- Timestamped and uniquely identified

Project notes:

- Research questions
- Hypotheses and predictions
- Study designs and protocols
- Progress tracking
- Decision logs
- Synthesis across sources

Meeting and discussion notes:

- Conference presentations
- Lab meetings
- Advisor discussions
- Peer feedback
- Collaboration ideas

Fleeting notes:

- Quick captures and ideas
- To be processed later
- Temporary holding area
- Thoughts during reading
- Questions for follow-up

**Annotation Features**:

Highlight and markup:

- Color-coded highlights
- Margin notes and comments
- Underline and strike-through
- Bookmarks for key sections
- Drawing and shapes on PDFs

Annotation metadata:

- Timestamp of annotation
- Author of annotation (for collaboration)
- Annotation type (question, insight, critique)
- Link to related annotations
- Tags for categorization

Export annotations:

- Extract all highlights and notes
- Generate annotation summary
- Export to markdown or JSON
- Preserve formatting and context
- Include source references

### Step 7: Search and Discovery Infrastructure

Implement powerful search capabilities:

**Search Features**:

Full-text search:

- Search across all document content
- Search within notes and annotations
- Search metadata fields
- Search tags and keywords
- Boolean operators (AND, OR, NOT)
- Proximity search (words near each other)

Advanced search filters:

- Filter by date range
- Filter by author(s)
- Filter by source type
- Filter by tags (multiple tags with AND/OR)
- Filter by reading status
- Filter by custom metadata fields

Semantic search:

- Find conceptually similar sources
- Search by meaning, not just keywords
- Expand queries with synonyms
- Find related topics automatically
- Question-answering over research corpus

Search results ranking:

- Relevance scoring
- Recency boost for newer sources
- Citation count weighting
- Personal ratings and importance
- Access frequency (often-used sources ranked higher)

**Discovery Features**:

Related sources suggestions:

- "Sources like this one"
- "Sources that cite this"
- "Sources by same authors"
- "Sources with similar tags"
- "Sources in same time period"

Research gap identification:

- Underexplored topics (few sources)
- Missing connections (should be related but aren't)
- Outdated sources needing updates
- Conflicting findings needing resolution
- Suggested reading to fill knowledge gaps

Trend detection:

- Emerging topics (growing rapidly)
- Hot topics (high current activity)
- Declining topics (less recent work)
- Stable topics (consistent coverage)
- Topic evolution over time

Saved searches and alerts:

- Save complex queries for reuse
- Set up alerts for new matching sources
- Subscribe to topic areas
- Monitor specific authors
- Track citation updates

### Step 8: Export and Integration with Knowledge Management Tools

Enable seamless export to popular PKM systems:

**Obsidian Export**:

```markdown
---
title: Paper Title
authors: [Author1, Author2]
year: 2024
tags: [machine-learning, neural-networks, deep-learning]
source: journal-article
doi: 10.1234/example
---

# Paper Title

## Summary
Main findings and arguments...

## Key Insights
- Insight 1
- Insight 2

## Methodology
Description of methods...

## Links
- [[Related Paper 1]]
- [[Related Paper 2]]

## References
Full citation...
```

Features:

- WikiLinks format for connections
- YAML frontmatter for metadata
- Folder structure preservation
- Graph view compatibility
- Tag support
- Backlinks functionality

**Notion Export**:

- Create database with properties
- Maintain relationships between pages
- Preserve hierarchical structure
- Export media and attachments
- Support for toggles and callouts
- Synced blocks for shared content

**Roam Research Export**:

- Block-based structure
- Bi-directional links with ((blocks))
- Daily notes integration
- Nested tags and hierarchies
- Query support
- Graph database format

**Other Formats**:

Markdown files:

- Portable plain text format
- Compatible with most editors
- Version control friendly
- Future-proof archival format

CSV/Excel:

- Tabular metadata export
- Bibliography lists
- Reading logs
- Citation analysis

JSON:

- Structured data export
- API integration
- Custom tool development
- Backup and archival

LaTeX/BibTeX:

- Academic writing integration
- Bibliography management
- Citation formatting
- Document compilation

### Step 9: Collaboration and Sharing Features

Enable team-based research organization:

**Shared Libraries**:

Multi-user access:

- Shared research database
- Real-time synchronization
- Conflict resolution
- Access permissions (read, write, admin)
- Activity tracking (who added what, when)

Collaborative annotation:

- Multiple users can annotate same source
- Attribution of notes to users
- Discussion threads on annotations
- Resolve/unresolve comments
- Notification of new annotations

Version control:

- Track changes to organization structure
- Revert to previous versions
- Branch/merge workflows
- Diff visualization
- Change history and audit log

**Sharing Options**:

Public sharing:

- Share individual sources or collections
- Generate shareable links
- Embeddable widgets
- Read-only access
- Citation attribution

Team workspaces:

- Project-based organization
- Role-based permissions
- Team tags and labels
- Shared search and filters
- Collaborative bibliographies

Export for sharing:

- Reading lists
- Annotated bibliographies
- Topic overviews
- Knowledge maps
- Teaching materials

### Step 10: Maintenance and Quality Assurance

Ensure research organization remains healthy and useful:

**Regular Maintenance Tasks**:

Content audits:

- Review rarely accessed sources
- Archive or remove outdated materials
- Update source metadata
- Verify file integrity and accessibility
- Check for duplicate entries

Structure optimization:

- Rebalance folder hierarchies
- Refine tag taxonomy
- Consolidate overlapping categories
- Split oversized folders
- Merge underutilized folders

Link validation:

- Check for broken internal links
- Verify external URL accessibility
- Update DOI links
- Fix orphaned sources
- Rebuild connection graphs

**Quality Metrics**:

Organization health score:

- Coverage: % of sources with complete metadata
- Connectivity: Average links per source
- Accessibility: Time to find specific source
- Activity: Recent additions and accesses
- Consistency: Adherence to naming conventions

User engagement metrics:

- Search success rate
- Average time to find information
- Most accessed sources and topics
- Tag usage frequency
- Contribution rate (for teams)

Growth and evolution tracking:

- Sources added per week/month
- Topic coverage expansion
- Citation network density
- Annotation volume
- Export frequency

Automated quality checks:

- Missing metadata fields
- Orphaned sources (no connections)
- Duplicate detection
- Stale content (not accessed in 1+ years)
- Inconsistent naming
- Broken links and references

## Usage Examples

### Example 1: Organize PhD Research by Topic

```bash
/research/organize --structure topic --tags --export obsidian
```

**Input**: Collection of 300 research papers on machine learning

```
Scattered PDFs in Downloads folder
Various bookmarks and web pages
Notes in different apps
Unorganized citations
```

**Output**: Structured Obsidian vault

```
ML Research/
├── Supervised Learning/
│   ├── Neural Networks/
│   │   ├── [[Attention Mechanisms - Vaswani 2017]].md
│   │   ├── [[Transformers - Brown 2020]].md
│   │   └── _index.md
│   └── Decision Trees/
├── Unsupervised Learning/
│   ├── Clustering/
│   └── Dimensionality Reduction/
└── Reinforcement Learning/
    ├── Q-Learning/
    └── Policy Gradients/

Tags: #neural-networks (45), #transformers (32), #attention (28)
Links: 1,234 bidirectional connections
Search Index: Full-text across all sources
```

### Example 2: Chronological Organization for Literature Review

```bash
/research/organize --structure chronological --generate-timeline
```

**Input**: 150 papers for systematic review on climate change

```
Papers from 1980s to present
Various authors and venues
Mixed methodologies
```

**Output**: Timeline-based organization

```
Climate Change Research Timeline/
├── Foundational Era (1980-2000)/
│   ├── Early Models/
│   │   ├── Hansen 1988 - Global Warming Projections
│   │   └── IPCC First Assessment 1990
│   └── _summary.md (15 papers, key developments)
├── Acceleration Period (2000-2010)/
│   ├── Improved Modeling/
│   └── Impacts Research/
├── Current Research (2010-2024)/
│   ├── Machine Learning Applications/
│   ├── Extreme Events/
│   └── Mitigation Strategies/
└── _synthesis.md

Visualization: Interactive timeline showing research evolution
Gap Analysis: Identified missing coverage in 2005-2008 period
```

### Example 3: Methodology-Based Organization for Meta-Analysis

```bash
/research/organize --structure methodology --filter peer-reviewed
```

**Input**: 200 studies for meta-analysis

```
Mixed study designs
Various sample sizes
Different analysis methods
```

**Output**: Method-categorized database

```
Meta-Analysis Database/
├── Randomized Controlled Trials/
│   ├── Large Scale (n>1000): 45 studies
│   │   ├── High Quality (Cochrane A): 32
│   │   └── Medium Quality (Cochrane B): 13
│   └── Small Scale (n<1000): 23 studies
├── Observational Studies/
│   ├── Prospective Cohort: 67 studies
│   └── Cross-Sectional: 34 studies
├── Systematic Reviews: 18 studies
└── Case Studies: 13 studies

Metadata extracted:
- Sample sizes, effect sizes, confidence intervals
- Risk of bias assessments
- Forest plot data
- Publication bias indicators
```

### Example 4: Create Zettelkasten-Style Knowledge Base

```bash
/research/organize --structure zettelkasten --atomic-notes
```

**Input**: Research notes and papers on neuroscience

```
Reading notes from 50 papers
Personal insights and connections
Questions and hypotheses
```

**Output**: Atomic note network

```
Zettelkasten/
├── Permanent Notes/
│   ├── 202501151430 - Synaptic plasticity mechanisms.md
│   │   Links: [[Long-term potentiation]], [[Memory formation]]
│   ├── 202501151445 - Hebbian learning principle.md
│   │   Links: [[Neural networks]], [[Synaptic plasticity]]
│   └── 202501151500 - Working memory capacity.md
│       Links: [[Prefrontal cortex]], [[Attention]]
├── Literature Notes/
│   ├── Kandel 2001 - Molecular biology of memory.md
│   └── Squire 2015 - Memory systems.md
└── Index Notes/
    ├── MOC - Memory and Learning.md (Map of Content)
    └── MOC - Neural Mechanisms.md

Network Stats:
- 127 permanent notes
- 50 literature notes
- 8 maps of content
- Average 4.2 links per note
- 15 clusters identified
```

### Example 5: Team Research Library with Tagging

```bash
/research/organize --collaborative --tags --permissions team
```

**Input**: Shared research for 5-person lab

```
Individual reading lists
Shared project papers
Meeting notes
Lab protocols
```

**Output**: Collaborative knowledge base

```
Lab Research Library/
├── Projects/
│   ├── Project Alpha/
│   │   ├── Background Reading/ (23 sources)
│   │   ├── Methodology/ (8 protocols)
│   │   └── Results/ (15 analyses)
│   └── Project Beta/
├── Individual Collections/
│   ├── Alice's Reading List/
│   ├── Bob's References/
│   └── Charlie's Notes/
└── Shared Resources/
    ├── Lab Protocols/
    └── Equipment Manuals/

Features:
- Real-time sync across team
- Activity feed (Alice added "Smith 2024")
- Shared tags: #project-alpha (67), #methods (45)
- Permissions: Read-all, Write-own-project
- Weekly digest emails
```

### Example 6: Export to Notion Database

```bash
/research/organize --export notion --include-metadata
```

**Input**: Organized research from Obsidian

```
150 papers with notes
Hierarchical folder structure
Tags and bidirectional links
```

**Output**: Notion database

```
Notion Database Properties:
├── Title (text)
├── Authors (multi-select)
├── Year (number)
├── Tags (multi-select)
├── Status (select: To Read, Reading, Completed)
├── Rating (select: ⭐⭐⭐⭐⭐)
├── Source Type (select)
├── DOI (URL)
├── Notes (rich text with links)
└── Related Papers (relation)

Views:
- Table: All papers with sortable columns
- Board: Kanban by reading status
- Timeline: Papers by publication year
- Gallery: Papers with thumbnail previews
```

### Example 7: Auto-Tag and Link Existing Research

```bash
/research/organize --auto-tag --generate-links --source ./research-pdfs/
```

**Input**: 500 unorganized PDFs

```
Raw PDFs with no metadata
Filenames like "download (1).pdf"
No organization or tags
```

**Output**: Fully tagged and linked collection

```
Processing Results:
✓ Extracted metadata from 487 PDFs (97% success)
✓ Generated 2,341 tags across 8 categories
✓ Created 5,678 bidirectional links
✓ Identified 45 topic clusters
✓ Detected 23 duplicate papers (removed)

Auto-Generated Organization:
├── Deep Learning (134 papers)
│   ├── Computer Vision (67)
│   │   └── Object Detection (23)
│   └── NLP (67)
├── Reinforcement Learning (89 papers)
├── Supervised Learning (156 papers)
└── Unsupervised Learning (95 papers)

Top Tags:
#neural-networks (234), #CNN (123), #transformers (89)

Hub Papers (most connected):
1. Vaswani 2017 - Attention Is All You Need (87 links)
2. He 2016 - ResNet (56 links)
3. Brown 2020 - GPT-3 (45 links)
```

## Quality Control Checklist

Before finalizing research organization, verify:

- [ ] All sources have complete metadata (title, author, year, type)
- [ ] Folder hierarchy is 3-4 levels deep (not too shallow or deep)
- [ ] Each folder contains between 3-10 items or subfolders
- [ ] All sources are in appropriate primary folder
- [ ] Tag taxonomy is consistent and well-defined
- [ ] No orphaned sources (sources with no connections)
- [ ] Bidirectional links are properly created and maintained
- [ ] Search index includes all sources and notes
- [ ] No duplicate sources detected
- [ ] File naming conventions are consistent
- [ ] README files exist for all major folders
- [ ] Citations are properly formatted and complete
- [ ] Notes are linked to their source materials
- [ ] Personal insights are distinguished from source content
- [ ] Privacy-sensitive information is protected
- [ ] Backup system is in place and tested
- [ ] Export functionality works for all target formats
- [ ] Collaboration permissions are correctly configured
- [ ] Search returns relevant results quickly (<2 seconds)
- [ ] Knowledge graph visualizes properly
- [ ] All external links and DOIs are accessible

## Best Practices

### Organizational Structure

- **Start with broad categories** and refine over time - it's easier to split folders than merge them
- **Maintain consistent depth** across your hierarchy - if Machine Learning has 3 levels, NLP should too for parallel structure
- **Use MECE principle** (Mutually Exclusive, Collectively Exhaustive) - each source should have one clear home
- **Limit folder depth to 3-4 levels** - deeper hierarchies are hard to navigate and maintain
- **Keep sibling folders balanced** - if one subfolder has 100 items and another has 2, restructure
- **Create index files** in each folder summarizing contents and providing navigation

### Tagging Strategy

- **Establish tag vocabulary upfront** - define core tags before mass-tagging to ensure consistency
- **Use hierarchical tags** when possible - #ml/supervised/neural-networks better than flat tags
- **Limit tags per source** to 5-10 - too many tags dilute their usefulness
- **Prefer specific over general** tags - #transformer is more useful than #neural-networks
- **Review tag usage quarterly** - remove tags used <3 times, merge similar tags
- **Create tag glossary** defining each tag's meaning and usage guidelines

### Note-Taking Excellence

- **Write in your own words** - don't just copy-paste, engage with the material
- **One concept per note** in Zettelkasten style - keeps notes atomic and reusable
- **Link early and often** - create connections as you discover them, not later
- **Include context in notes** - future you won't remember why you thought something was important
- **Timestamp fleeting notes** and process within 48 hours before context fades
- **Separate facts from opinions** - clearly mark your interpretations vs source claims

### Link Management

- **Link explicitly** when certain, tag implicitly when unsure - links are stronger assertions
- **Use descriptive link text** - not "see [[this]]" but "extends [[Smith's framework]]"
- **Bi-directional links for relationships** - if A relates to B, both should know about each other
- **Create hub notes** for major topics that collect related sources
- **Review link graph monthly** - identify clusters, bridges, and missing connections
- **Don't over-link** - only link when there's meaningful relationship, not just shared keywords

### Search and Discovery

- **Use saved searches** for recurring queries - "papers to read this month", "high-priority sources"
- **Tag search history** to identify research patterns and gaps
- **Set up alerts** for new sources matching your interests
- **Leverage semantic search** to find conceptually related work, not just keyword matches
- **Create topic dashboards** showing status, recent additions, top sources for key areas
- **Export search results** as collections for specific projects or questions

### Maintenance Cadence

- **Daily**: Add new sources, create fleeting notes, quick captures
- **Weekly**: Process fleeting notes into permanent notes, create links, tag new sources
- **Monthly**: Review tag taxonomy, validate links, check for duplicates, assess organization health
- **Quarterly**: Major structure refactoring, archive old projects, export backups, team sync
- **Annually**: Comprehensive audit, technology migration planning, long-term strategy review

### Collaboration Best Practices

- **Establish team conventions** before importing personal libraries - agree on tags, structure, naming
- **Use permissions wisely** - everyone can read and annotate, but limit structure changes to designated curators
- **Create shared tags** for team use vs personal tags for individual organization
- **Regular team reviews** of shared collections ensure quality and relevance
- **Document decisions** about organization structure and taxonomy in README files
- **Respect others' notes** - don't edit others' annotations, instead add your own perspective

### Tool Selection

- **Choose tools you'll actually use** - the best system is the one you maintain, not the most feature-rich
- **Prioritize plain text** formats (Markdown) for longevity and portability
- **Ensure easy export** - avoid lock-in to proprietary formats
- **Test at small scale** before committing entire library to new tool
- **Version control** your knowledge base with Git for backup and history
- **Separate capture from organization** - quick inbox for new items, separate time for organization

### Avoiding Common Pitfalls

- **Don't over-organize prematurely** - some chaos is OK, structure emerges from use
- **Avoid perfectionism** - done is better than perfect, you can always refactor
- **Don't let tagging become busywork** - focus on tags that aid actual search and discovery
- **Resist tool-hopping** - pick a system and stick with it for 6+ months before switching
- **Don't silo by project** - cross-project connections often yield best insights
- **Avoid orphaning** - when archiving projects, preserve valuable sources in main library

## Integration Points

### Related Commands

- `/research/gather` - Collect sources that will be organized into knowledge base
- `/research/cite` - Generate citations for organized sources
- `/research/annotate` - Add notes and highlights to organized materials
- `/research/summarize` - Create summaries of organized collections

### Tool Integrations

- **Obsidian**: Markdown-based PKM with graph view and linking
- **Notion**: Database-driven knowledge base with rich media
- **Roam Research**: Networked thought tool with block-level links
- **Zotero**: Reference manager that integrates with note-taking
- **Logseq**: Open-source alternative to Roam with local-first storage
- **DEVONthink**: AI-powered document management for macOS
- **Evernote**: Note-taking with powerful search and web clipper
- **OneNote**: Microsoft's note-taking with handwriting support

### Workflow Connections

1. **Research** → `/research/gather` → `/research/organize` → **Structured Knowledge Base**
2. **Papers** → `/research/organize --auto-tag` → **Tagged Library** → Easy Discovery
3. **Notes** → `/research/organize --zettelkasten` → **Atomic Notes** → Novel Insights
4. **Team Research** → `/research/organize --collaborative` → **Shared Library** → Team Alignment
5. **Organized Library** → `/research/organize --export obsidian` → **Obsidian Vault** → Writing

## Advanced Features

### AI-Powered Organization

Leverage machine learning for intelligent organization:

- Auto-categorize sources by topic using NLP
- Suggest tags based on content analysis
- Detect semantic similarity for linking
- Identify research trends and emerging topics
- Recommend reading order based on dependencies
- Generate automatic summaries of collections

### Knowledge Graph Analytics

Deep analysis of research connections:

- Identify influential papers (high PageRank)
- Find knowledge gaps (sparse regions)
- Detect research communities (graph clustering)
- Trace idea evolution (citation chains)
- Predict relevant future reading
- Visualize topic landscapes

### Automated Workflows

Set up automated research organization:

- Watch folders for new PDFs → auto-import and tag
- Email to knowledge base integration
- Browser extension for one-click saving
- Scheduled metadata updates from APIs
- Automatic duplicate detection and merging
- Smart inbox processing with AI triage

### Multi-Modal Organization

Beyond text-based research:

- Image and diagram extraction from papers
- Video lecture notes with timestamps
- Podcast episode tagging and transcription
- Dataset cataloging and versioning
- Code snippet libraries linked to papers
- Experimental protocols and lab notebooks

## Common Use Cases

### Dissertation Research Management

Use case: PhD student organizing 500+ sources across 4 years
Solution: Topic-based structure → Zettelkasten notes → Timeline view → Regular refactoring

### Systematic Literature Review

Use case: Conducting PRISMA-compliant systematic review
Solution: Methodology organization → Quality scoring → Inclusion/exclusion tracking → Export to review manager

### Research Lab Knowledge Base

Use case: 10-person lab with 5 concurrent projects
Solution: Collaborative workspace → Project-based folders → Shared protocols → Activity tracking

### Academic Writing Project

Use case: Writing book requiring 200+ sources
Solution: Chapter-based organization → Argument mapping → Citation tracking → Thematic collections

### Professional Learning Portfolio

Use case: Industry researcher tracking field developments
Solution: Chronological organization → Trend detection → Reading lists → Newsletter generation

### Grant Proposal Preparation

Use case: Assembling evidence for research proposal
Solution: Topic clustering → Gap analysis → Recent work filtering → Bibliography export

### Teaching Material Development

Use case: Professor organizing resources for course
Solution: Module-based structure → Difficulty tagging → Learning objectives mapping → Student sharing

### Interdisciplinary Research

Use case: Bridging multiple fields (e.g., AI + Healthcare)
Solution: Multi-dimensional tagging → Cross-domain linking → Terminology mapping → Knowledge translation

### Competitive Intelligence

Use case: Tracking competitor research and patents
Solution: Organization tracking → Chronological monitoring → Technology area mapping → Alert system

### Personal Knowledge Management

Use case: Lifelong learner curating diverse interests
Solution: Interest-based organization → Serendipitous linking → Quarterly reviews → Blog post generation

## Troubleshooting

### Overwhelmed by Volume

**Problem**: Too many sources to organize effectively
**Solutions**:

- Start with recent and most relevant (80/20 rule)
- Use auto-tagging to bootstrap organization
- Batch process by project or time period
- Archive low-priority sources for later
- Focus on sources you'll actually reference

### Unclear Organization Structure

**Problem**: Can't decide how to organize research
**Solutions**:

- Start with simplest structure that works
- Let structure emerge from usage patterns
- Ask: "How will I search for this later?"
- Copy structure from successful similar projects
- Test with 50 sources before committing

### Inconsistent Tagging

**Problem**: Tags are messy and hard to use
**Solutions**:

- Create tag vocabulary guide
- Use tag auto-complete to prevent variations
- Quarterly tag cleanup and consolidation
- Limit who can create new tags (in teams)
- Prefer existing tags over creating new ones

### Broken Links

**Problem**: Links between sources not working
**Solutions**:

- Run link validation tool
- Use relative paths not absolute
- Implement broken link monitoring
- Create link maintenance routine
- Use IDs instead of titles for linking

### Export Issues

**Problem**: Exported organization doesn't work in target tool
**Solutions**:

- Test export with small sample first
- Check format compatibility documentation
- Use intermediary formats (Markdown, JSON)
- Manual cleanup of exported content
- Contact tool support for import help

### Collaboration Conflicts

**Problem**: Team members organize differently
**Solutions**:

- Establish team conventions document
- Designate organization curator role
- Regular team sync meetings
- Use personal spaces for individual organization
- Compromise on hybrid approach

## Success Criteria

### Organization Quality

- 95%+ of sources have complete metadata
- Average 3-5 relevant tags per source
- Clear folder hierarchy (3-4 levels)
- No duplicate sources
- All sources accessible within 30 seconds

### Connectivity

- Average 3+ links per source
- <5% orphaned sources (no connections)
- Knowledge graph shows clear clusters
- Hub sources properly identified
- Cross-references validated

### Usability

- Search results returned in <2 seconds
- 90%+ search success rate (find what you need)
- Intuitive navigation structure
- Consistent naming conventions
- Easy onboarding for new users

### Maintenance

- Weekly update routine established
- Monthly structure review completed
- Quarterly tag cleanup performed
- Backups automated and tested
- Health metrics monitored

### Team Collaboration

- All team members actively contributing
- <24 hour sync time for changes
- Clear ownership and permissions
- Regular team reviews scheduled
- Shared conventions documented

### ROI Metrics

- 70%+ reduction in time finding sources
- 3x faster literature review process
- 50%+ increase in cross-source insights
- Zero lost sources or notes
- Measurable productivity improvements
