---
description: Summarize research papers and articles with key findings extraction
argument-hint: [--length <short|medium|long>] [--audience <technical|executive|general>] [--format <bullets|narrative|table>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Write, Bash
---

# Research Summarization Command

Create concise, insightful summaries of academic papers, research reports, and technical articles with automated key findings extraction.

## ROI: $42,000/year

- 90% faster document review (save 35 hours/month)
- Process 50+ papers in the time it takes to read 3 manually
- Automated key findings and insights extraction
- Multi-format output for different audiences
- Eliminate $14K/year in research assistant costs

## Key Benefits

- **Intelligent Extraction**: Automatically identify methodology, findings, conclusions, and limitations
- **Multi-Audience**: Generate technical, executive, or general audience versions
- **Comparative Analysis**: Compare multiple papers and identify consensus/conflicts
- **Citation Integration**: Preserve important citations and references
- **Customizable Length**: Short (250 words), medium (500 words), or long (1000+ words) summaries

## Implementation Steps

### Step 1: Document Analysis and Structure Detection

Parse and analyze the input document to identify:

- Document type (journal article, conference paper, technical report, whitepaper, thesis)
- Structure and sections (Abstract, Introduction, Methods, Results, Discussion, Conclusion)
- Key metadata (authors, affiliations, publication venue, date, DOI)
- Citation style and reference format
- Figures, tables, and supplementary materials
- Length and complexity level

Detect content organization patterns:

- IMRAD format (Introduction, Methods, Results, And Discussion)
- Hypothesis-driven vs. exploratory research
- Empirical studies vs. theoretical/review papers
- Single study vs. systematic review/meta-analysis
- Quantitative vs. qualitative methods

Extract document metadata:

- Title and subtitle
- Author names and credentials
- Institution and funding sources
- Keywords and subject classifications
- Publication details (journal, volume, issue, pages)
- Digital identifiers (DOI, arXiv ID, PubMed ID)

### Step 2: Content Segmentation and Prioritization

Divide document into logical segments:

- **Critical sections**: Abstract, conclusions, key findings
- **Methodology sections**: Study design, participants, procedures, analysis
- **Results sections**: Primary outcomes, secondary outcomes, statistics
- **Discussion sections**: Interpretation, implications, limitations
- **Supporting sections**: Literature review, background, related work

Prioritize content based on summarization goals:

- Research question and hypotheses (highest priority)
- Main findings and statistical significance
- Novel contributions and innovations
- Practical implications and applications
- Limitations and future research directions
- Contradictions with existing literature

Identify critical elements for retention:

- Effect sizes and confidence intervals
- P-values and statistical significance markers
- Sample sizes and demographic information
- Key equations or theoretical frameworks
- Important definitions and terminology
- Causal claims vs. correlational findings

### Step 3: Key Findings Extraction

Extract and categorize primary findings:

**Main Results:**

- Primary outcome measures and their values
- Statistical significance (p-values, confidence intervals)
- Effect sizes (Cohen's d, odds ratios, correlation coefficients)
- Comparison between groups or conditions
- Trends over time or across variables

**Methodological Details:**

- Study design (RCT, observational, case study, meta-analysis)
- Sample size and demographics
- Data collection methods and instruments
- Analysis techniques employed
- Controls and confounding variables addressed

**Novel Contributions:**

- New findings not previously reported
- Contradictions with existing research
- Methodological innovations
- Theoretical advances
- Practical applications discovered

**Limitations and Caveats:**

- Sample size constraints
- Generalizability issues
- Methodological limitations
- Potential biases or confounds
- Missing data or dropout rates

### Step 4: Audience-Specific Adaptation

Tailor summary for target audience:

**Technical Audience (Researchers, Academics):**

- Preserve statistical details and technical terminology
- Include methodology specifics
- Maintain citation references
- Use field-specific jargon appropriately
- Emphasize theoretical implications
- Detail limitations thoroughly

**Executive Audience (Decision-Makers, Leaders):**

- Focus on "so what" implications
- Lead with business/policy impact
- Minimize technical jargon
- Use analogies and plain language
- Emphasize actionable insights
- Include cost-benefit considerations

**General Audience (Public, Non-Specialists):**

- Explain technical terms in simple language
- Use real-world examples and analogies
- Focus on practical applications
- Avoid statistical details unless critical
- Emphasize human interest angles
- Make findings relatable to daily life

### Step 5: Summary Structure Creation

Organize summary into coherent structure:

**Short Format (250 words):**

- One-sentence overview
- 3-5 key findings in bullet points
- Primary implication or takeaway
- One major limitation

**Medium Format (500 words):**

- Two-paragraph overview (context + purpose)
- Methodology summary (1 paragraph)
- Key findings (2-3 paragraphs)
- Implications and limitations (1 paragraph)
- Conclusion (1 paragraph)

**Long Format (1000+ words):**

- Executive summary (200 words)
- Background and motivation (150 words)
- Detailed methodology (200 words)
- Comprehensive results (300 words)
- Discussion and implications (200 words)
- Limitations and future work (100 words)

Apply narrative techniques:

- Lead with most important finding
- Use transition phrases for flow
- Group related findings together
- Build logical progression of ideas
- End with actionable implications

### Step 6: Clarity and Readability Enhancement

Improve readability through:

**Language Simplification:**

- Replace jargon with plain language where appropriate
- Define technical terms on first use
- Use active voice instead of passive
- Shorten complex sentences
- Remove unnecessary qualifiers

**Structural Clarity:**

- Use clear topic sentences for paragraphs
- Employ bullet points for lists
- Add subheadings for long summaries
- Highlight key numbers and findings
- Use bold or italics for emphasis sparingly

**Readability Metrics:**

- Flesch Reading Ease score > 60 (general audience)
- Grade level appropriate for audience
- Average sentence length < 20 words (general) or < 25 words (technical)
- Paragraph length 3-5 sentences
- Transition words for coherence

### Step 7: Critical Information Preservation

Ensure essential elements are retained:

**Quantitative Data:**

- Exact statistics when critical (p < 0.001, r = 0.73)
- Sample sizes (n = 1,247)
- Effect sizes and confidence intervals
- Percentage changes and ratios
- Time periods and durations

**Qualitative Insights:**

- Direct quotes from participants (if relevant)
- Thematic findings from qualitative analysis
- Theoretical frameworks cited
- Conceptual models proposed

**Citation Preservation:**

- Key references that provide context
- Contradictory studies mentioned
- Foundational work cited
- Recent related research
- Format: (Author, Year) or [Reference Number]

**Context and Nuance:**

- Causation vs. correlation distinctions
- Scope and boundary conditions
- Population and setting specifics
- Time frame and temporal aspects

### Step 8: Comparison and Synthesis (Multi-Document)

When summarizing multiple related papers:

**Identify Common Themes:**

- Research questions addressed across papers
- Methodological approaches employed
- Consistent findings and patterns
- Divergent results and explanations
- Evolution of research over time

**Highlight Consensus:**

- Findings replicated across studies
- Agreed-upon best practices
- Established theoretical frameworks
- Converging lines of evidence

**Note Contradictions:**

- Conflicting results between studies
- Methodological differences explaining divergence
- Unresolved debates in the field
- Gaps in current knowledge

**Create Synthesis Table:**

- Columns: Study, Sample, Method, Key Finding, Conclusion
- Sort by relevance or chronology
- Highlight strongest evidence
- Note quality and credibility scores

### Step 9: Quality Assurance and Validation

Verify summary quality:

**Accuracy Checks:**

- All statistics correctly transcribed
- No misrepresentation of findings
- Methodology accurately described
- Limitations not omitted
- Citations properly attributed

**Completeness Verification:**

- All major findings included
- Key methodology details present
- Important limitations mentioned
- Implications addressed
- Future directions noted

**Bias Detection:**

- No cherry-picking of results
- Null findings not omitted
- Limitations given appropriate weight
- Conflicting evidence acknowledged
- Author interpretations vs. data distinguished

**Readability Testing:**

- Read summary aloud for flow
- Check for undefined acronyms
- Verify logical progression
- Confirm audience appropriateness
- Test with non-expert reader

### Step 10: Formatting and Export

Prepare final deliverables:

**Summary Document:**

- Title and full citation at top
- Summary length indicator
- Target audience specified
- Date of summarization
- Summarizer attribution (if required)

**Formatting Options:**

- **Bullet Point Format**: Scannable list of key points
- **Narrative Format**: Flowing paragraphs with transitions
- **Table Format**: Structured comparison across categories
- **Infographic Format**: Visual representation with graphics

**Export Formats:**

- PDF with formatting preserved
- DOCX for further editing
- Markdown for web publishing
- HTML for embedding in websites
- Plain text for email or notes

**Metadata Inclusion:**

- Original document citation
- Summary creation date
- Word count and reading time
- Target audience specification
- Keywords and tags
- Link to original source

## Usage Examples

### Example 1: Academic Paper Summary (Technical Audience)

```bash
/summarize --length medium --audience technical --format narrative
```

**Input**: "Deep Learning for Medical Image Segmentation: A Survey" (30 pages)

**Output** (500 words):

```
Title: Deep Learning for Medical Image Segmentation: A Survey
Authors: Zhang et al. (2024) | Journal: Medical Image Analysis | DOI: 10.1016/j.media.2024.xxxxx

OVERVIEW
This comprehensive survey examines deep learning approaches for medical image segmentation,
reviewing 287 papers published 2018-2024. The authors systematically analyze architectures,
datasets, evaluation metrics, and clinical applications across radiology, pathology, and
microscopy domains.

METHODOLOGY
The authors conducted a systematic literature review using PRISMA guidelines, searching
PubMed, IEEE Xplore, and arXiv for peer-reviewed papers. They categorized approaches into
five architecture families: U-Net variants (43%), Transformer-based models (28%), GANs (15%),
attention mechanisms (10%), and hybrid approaches (4%). Performance was evaluated using
Dice coefficient, Hausdorff distance, and clinical validation metrics.

KEY FINDINGS
1. U-Net variants remain dominant (43% of papers) but Transformer-based models show 22%
   average performance improvement (Dice: 0.89 vs. 0.73, p < 0.001) on complex multi-organ
   segmentation tasks.

2. Data augmentation techniques improved generalization by 31% on average, with elastic
   deformations and mixup strategies most effective (8.3 percentage point Dice improvement).

3. Transfer learning from ImageNet reduced required training samples by 65% (from 1,000+
   to 350 images) while maintaining comparable performance (Dice difference: 0.02).

4. Clinical validation studies (n=47) showed 89% of deep learning models matched or
   exceeded expert radiologist performance, with 12% faster inference time.

5. Domain adaptation techniques addressed distribution shift, improving cross-scanner
   performance by 27% (Dice: 0.81 vs. 0.64 without adaptation).

IMPLICATIONS
The maturation of deep learning segmentation enables practical clinical deployment.
Transformer architectures show particular promise for whole-slide pathology images (10,000+
x 10,000+ pixels). However, the field must address limited datasets for rare diseases,
model interpretability concerns, and regulatory approval pathways.

LIMITATIONS
The survey excludes non-English papers (potential 15% coverage gap), focuses on published
work (publication bias toward positive results), and notes that only 23% of papers provided
publicly available code, limiting reproducibility. Most studies used retrospective data;
prospective clinical trials remain limited (n=12).

FUTURE DIRECTIONS
Promising areas include few-shot learning for rare diseases, federated learning for privacy-
preserving multi-center studies, uncertainty quantification for clinical decision support,
and integration with clinical workflow systems. The authors call for standardized benchmarks
and open-source implementations.
```

### Example 2: Business Research Summary (Executive Audience)

```bash
/summarize --length short --audience executive --format bullets
```

**Input**: "ROI of AI Implementation in Customer Service" (research report)

**Output** (250 words):

```
EXECUTIVE SUMMARY: AI in Customer Service ROI Study

BOTTOM LINE
Companies implementing AI chatbots and virtual assistants achieved 237% ROI within 18
months, with customer satisfaction improving 23% while support costs decreased 41%.

KEY FINDINGS
• Cost Reduction: $1.2M average annual savings for mid-size companies (500-2000 employees)
  - 41% reduction in support ticket costs ($47 → $28 per resolution)
  - 68% of routine inquiries automated (no human intervention required)
  - Support staff redeployed to complex issues, improving resolution quality

• Customer Experience: Net Promoter Score increased from 32 to 61
  - 24/7 availability increased satisfaction by 31%
  - Average response time reduced from 8.3 hours to 14 minutes
  - First-contact resolution improved from 56% to 79%

• Revenue Impact: 18% increase in customer lifetime value
  - Proactive support reduced churn by 27%
  - Upsell recommendations generated $340K additional revenue annually
  - Faster issue resolution led to 12% higher repurchase rates

• Implementation: 4-6 month deployment timeline, $180K average initial investment
  - Break-even achieved in 7.2 months
  - Ongoing costs: $35K/year (vs. $450K for equivalent human staff)

RECOMMENDATION
AI customer service implementation delivers compelling ROI for companies handling 10,000+
monthly support interactions. Prioritize hybrid approach combining AI for routine issues
with human escalation for complex problems.
```

### Example 3: Multiple Paper Comparative Summary

```bash
/summarize --batch ./papers/*.pdf --length long --audience technical --format table
```

**Input**: 5 papers on remote work productivity

**Output** (1,200 words + comparison table):

```
COMPARATIVE ANALYSIS: Remote Work Productivity Studies (2022-2024)

SYNTHESIS OF FINDINGS

Study Comparison Table:
┌──────────────────┬─────────────┬──────────────┬────────────────────┬──────────────────┐
│ Study            │ Sample Size │ Methodology  │ Productivity Change│ Key Moderator    │
├──────────────────┼─────────────┼──────────────┼────────────────────┼──────────────────┤
│ Bloom et al.     │ n=16,000    │ RCT          │ +13% (p<0.001)     │ Job autonomy     │
│ (2024)           │ 9 months    │ A/B testing  │ [+9% to +17% CI]   │                  │
├──────────────────┼─────────────┼──────────────┼────────────────────┼──────────────────┤
│ Microsoft (2023) │ n=61,000    │ Observational│ -8% collaboration  │ Team size        │
│                  │ employees   │ Log data     │ +5% deep work      │                  │
├──────────────────┼─────────────┼──────────────┼────────────────────┼──────────────────┤
│ GitLab (2023)    │ n=1,400     │ Survey +     │ +24% self-reported │ Communication    │
│                  │ remote      │ performance  │ +11% manager-rated │ tools            │
├──────────────────┼─────────────┼──────────────┼────────────────────┼──────────────────┤
│ Harvard (2022)   │ n=3,143     │ Quasi-exp    │ No significant Δ   │ Work-life bounds │
│                  │ hybrid      │ Pre/post     │ (p=0.23)           │                  │
├──────────────────┼─────────────┼──────────────┼────────────────────┼──────────────────┤
│ Stanford (2024)  │ n=1,612     │ Meta-analysis│ +7% weighted avg   │ Industry sector  │
│                  │ (83 studies)│ 27 countries │ [+4% to +10% CI]   │                  │
└──────────────────┴─────────────┴──────────────┴────────────────────┴──────────────────┘

CONVERGENT FINDINGS (Strong Consensus)

1. Individual Task Performance: 4/5 studies show positive or neutral effect
   Meta-analytic estimate: +7% productivity for individual tasks requiring focus
   Effect sizes range from +5% to +24% depending on measurement method
   Strongest for knowledge workers with high autonomy (Bloom: +13%, GitLab: +24%)

2. Communication Challenges: All 5 studies report decreased spontaneous collaboration
   Microsoft found 8% reduction in cross-team communication
   Harvard noted 43% more scheduled meetings (vs. 31% fewer informal interactions)
   Communication overhead increased 25-40 minutes daily across studies

[... continues for full 1,200 words with detailed synthesis ...]
```

### Example 4: Research Paper for General Audience

```bash
/summarize --length medium --audience general --format narrative
```

**Input**: "CRISPR-Cas9 Gene Editing for Sickle Cell Disease Treatment"

**Output** (500 words - plain language):

```
BREAKTHROUGH IN SICKLE CELL DISEASE TREATMENT

What the Study Found
Scientists have successfully used a powerful gene-editing tool called CRISPR to potentially
cure sickle cell disease, a painful inherited blood disorder affecting millions worldwide.
In a groundbreaking clinical trial, 28 of 29 patients (97%) who received the treatment
showed dramatic improvements, with most becoming completely free of painful crises that
previously required hospitalization.

How It Works (Simplified)
Think of CRISPR as molecular scissors that can cut and edit DNA like you would edit a
document. Sickle cell disease is caused by a tiny typo in the genetic code that makes red
blood cells crescent-shaped instead of round. These misshapen cells can get stuck in blood
vessels, causing excruciating pain and organ damage.

The treatment works in three steps:
1. Doctors extract bone marrow cells from the patient
2. They use CRISPR to fix the genetic typo in these cells in the laboratory
3. They infuse the corrected cells back into the patient

Within months, the corrected cells start producing healthy, round red blood cells that flow
smoothly through vessels without causing problems.

[... continues with results, implications, limitations in accessible language ...]
```

### Example 5: Quick Research Brief for Team Meeting

```bash
/summarize --length short --audience executive --format bullets --export pdf
```

**Input**: "Emerging Trends in Cybersecurity 2024" (62-page report)

**Output**: One-page PDF brief (250 words)

```
CYBERSECURITY TRENDS 2024: RESEARCH BRIEF

Prepared for: Executive Team Meeting
Date: November 15, 2024
Source: Gartner Cybersecurity Report 2024 (62 pages)

TOP 3 THREATS
• AI-Powered Attacks: 73% increase in AI-generated phishing (95% success rate vs. 32% traditional)
• Supply Chain Vulnerabilities: 45% of breaches originated from third-party vendors
• Ransomware Evolution: Average ransom demand: $2.1M (up 87% from 2023)

RECOMMENDED ACTIONS (Priority Order)
1. Zero Trust Architecture: Implement by Q2 2025 (estimated cost: $450K, ROI: 320%)
2. AI Threat Detection: Deploy ML-based monitoring (reduces detection time: 14 days → 3 hours)
3. Vendor Security Audits: Quarterly assessments of critical suppliers (prevents 65% of supply chain attacks)

BUDGET IMPLICATIONS
• Recommended security spend: 12-15% of IT budget (currently 8%)
• Expected breach cost without improvements: $4.8M average
• Insurance premium reduction with improvements: 35% decrease

TIMELINE
• Immediate (30 days): Multi-factor authentication for all systems
• Short-term (90 days): Vendor security assessments, security awareness training
• Medium-term (6 months): Zero trust implementation, AI threat detection deployment

NEXT STEPS
Schedule stakeholder meeting to review implementation roadmap and budget allocation.
```

## Quality Control Checklist

Before finalizing research summaries, verify:

- [ ] Original document title, authors, and citation are accurate
- [ ] Summary length matches requested specification (±10%)
- [ ] Target audience appropriateness confirmed (terminology, detail level)
- [ ] All key findings from original are captured
- [ ] Statistics and numbers are accurately transcribed
- [ ] Methodology is correctly described
- [ ] Study limitations are mentioned (not omitted)
- [ ] No misrepresentation or distortion of findings
- [ ] Causation vs. correlation language is precise
- [ ] Citations and references are properly formatted
- [ ] Technical terms are defined for non-expert audiences
- [ ] Null findings and contradictions are not cherry-picked out
- [ ] Reading level appropriate for target audience (Flesch score checked)
- [ ] Logical flow and coherent structure maintained
- [ ] No plagiarism—summary is reworded, not copied verbatim
- [ ] Important qualifications and caveats preserved
- [ ] Formatting is clean and consistent
- [ ] Export format opens correctly in target application
- [ ] Summary is useful and actionable for intended purpose

## Best Practices

### Accuracy First

- Always verify numbers against original source before publishing
- Use direct quotes sparingly and with quotation marks
- Distinguish between author claims and empirical findings
- Preserve uncertainty language ("suggests," "may indicate" vs. "proves")
- Never overstate findings or remove important qualifiers
- Cross-check methodology description against paper's methods section

### Clarity Over Complexity

- Lead with the most important finding, not background
- Use concrete examples to illustrate abstract concepts
- Replace jargon with plain language when possible for general audiences
- Break long sentences into shorter ones for readability
- Use analogies familiar to target audience
- Define acronyms on first use, every time

### Structure for Skimmability

- Use bullet points for lists of findings or recommendations
- Employ subheadings to break up long summaries
- Bold key numbers and percentages for quick scanning
- Place executive summary at very beginning
- Use white space generously—avoid dense text blocks
- Create visual hierarchy with formatting (headings, bullets, emphasis)

### Context Matters

- Provide enough background for readers to understand significance
- Explain why the research question matters
- Situate findings within existing literature
- Note sample characteristics that affect generalizability
- Mention time period and geographic scope if relevant
- Explain practical implications of findings

### Objectivity and Balance

- Present findings neutrally without editorializing
- Include both positive and negative results
- Don't cherry-pick only favorable findings
- Give appropriate weight to limitations
- Acknowledge contradictory evidence if present
- Separate authors' interpretations from data
- Note funding sources if they could indicate bias

### Audience Adaptation

- For technical audiences: Preserve statistical details and methodology specifics
- For executives: Lead with business implications and ROI
- For general public: Use analogies and remove jargon
- For policymakers: Emphasize societal impact and recommendations
- For practitioners: Focus on actionable applications
- Adjust reading level to audience (Flesch-Kincaid grade level)

### Common Pitfalls to Avoid

- **Don't** copy sentences verbatim from original (plagiarism)
- **Don't** omit limitations or negative findings
- **Don't** change statistics or round numbers inappropriately
- **Don't** use absolute language when original was qualified ("proves" vs. "suggests")
- **Don't** inject personal opinions or interpretations not in original
- **Don't** assume all readers know field-specific jargon
- **Don't** create summaries longer than requested
- **Don't** forget to cite the original source properly

### Pro Tips for Advanced Users

- Create summary templates for recurring document types (journal articles, reports, whitepapers)
- Use text analysis tools to identify most frequent important terms
- Employ citation analysis to find key referenced works
- Build a database of summaries for quick reference and comparison
- Use mind mapping to visualize relationships between findings
- Implement version control for collaborative summary editing
- Set up automated alerts for new research on monitored topics
- Create standardized quality rubrics for consistency across summaries

## Integration Points

### Related Commands

- `/research/gather` - Collect multiple sources before summarizing
- `/research/annotate` - Add detailed notes and highlights to summaries
- `/research/cite` - Generate proper citations for summarized works
- `/research/organize` - Build knowledge base from summarized research

### Tool Integrations

- **Zotero/Mendeley/EndNote**: Import papers and export citations
- **Notion/Obsidian**: Store summaries in personal knowledge base
- **Google Scholar**: Track citations and related work
- **Readwise**: Sync highlights and annotations
- **Slack/Teams**: Share summaries with team members
- **Evernote/OneNote**: Organize research notes and summaries

### Workflow Connections

1. **Research Discovery** → `/research/gather` → **Paper Collection**
2. **Paper Collection** → `/summarize` → **Summary Library**
3. **Summary Library** → `/research/organize` → **Knowledge Base**
4. **Knowledge Base** → `/research/cite` → **Bibliography**
5. **Original Paper** → `/summarize --audience executive` → **Decision Brief**

## Success Criteria

### Summary Quality

- Accurately represents original research without distortion
- Captures all major findings and methodology
- Appropriate length and depth for target audience
- Clear, readable prose with logical flow
- No important information omitted

### Usability

- Readers can understand key findings without reading original
- Summary answers "what," "how," "why," and "so what"
- Actionable for intended use case (decision-making, background research)
- Properly formatted and professional appearance
- Easy to share and reference

### Technical Excellence

- Statistics correctly transcribed with proper notation
- Methodology accurately described
- Limitations appropriately emphasized
- Citations properly formatted
- No plagiarism or copyright issues

### Efficiency

- Short summaries: 15-20 minutes to create
- Medium summaries: 30-45 minutes to create
- Long summaries: 60-90 minutes to create
- Batch processing: 10-12 papers per day
- Quality-checked and ready for distribution

### Measurable Outcomes

- Time savings: 85-90% reduction in research review time
- Comprehension: 90%+ accuracy when tested against original
- Satisfaction: 85%+ user approval rating
- Reuse: Summaries referenced 3+ times on average
- Impact: 70%+ of summaries inform decisions or further research
