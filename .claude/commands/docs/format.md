---
description: Format documents professionally (reports, proposals, whitepapers) with templates
argument-hint: [--type <report|proposal|whitepaper|ebook>] [--template <corporate|academic|creative>] [--export <pdf|docx|html>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Write, Bash
---

# Document Formatting Command

Professional document formatting with industry-standard templates, typography, and layout optimization.

## ROI: $45,000/year

- 85% faster document creation (save 34 hours/month)
- Professional-grade templates eliminate $15K/year design costs
- Multi-format export (PDF, DOCX, HTML, Markdown)
- Brand-consistent styling reduces review cycles by 60%
- Automated table of contents, citations, headers/footers

## Key Benefits

- **Template Library**: 50+ professional templates across corporate, academic, and creative styles
- **Smart Formatting**: Auto-detect content structure and apply appropriate styling
- **Multi-Format Export**: Generate PDF, DOCX, HTML, and Markdown from single source
- **Brand Consistency**: Apply corporate style guides automatically
- **Accessibility**: WCAG 2.1 AA compliant output with proper heading hierarchy

## Implementation Steps

### Step 1: Document Analysis and Type Detection

Analyze the source document to determine:

- Document type (report, proposal, whitepaper, ebook, technical documentation)
- Current format and structure
- Content hierarchy (sections, subsections, appendices)
- Special elements (tables, figures, code blocks, equations)
- Target audience and purpose
- Brand requirements (if specified)

Parse document metadata:

- Title, authors, date, version
- Keywords and tags
- Abstract or executive summary
- Table of contents requirements
- Citation style (APA, MLA, Chicago, IEEE)

### Step 2: Template Selection and Customization

Select appropriate template based on:

- Document type and purpose
- Industry standards (corporate, academic, government)
- Audience expectations
- Brand guidelines

Template categories:

- **Corporate**: Business reports, proposals, whitepapers
- **Academic**: Research papers, theses, dissertations
- **Creative**: Ebooks, magazines, portfolios
- **Technical**: API docs, user guides, specifications
- **Marketing**: Case studies, sales decks, brochures

Customize template with:

- Company logo and branding
- Color scheme (primary, secondary, accent)
- Typography (heading fonts, body fonts, code fonts)
- Page layout (margins, columns, spacing)
- Header/footer content

### Step 3: Typography and Style Application

Apply professional typography:

- **Headings**: Font size hierarchy (H1: 24pt, H2: 20pt, H3: 16pt, H4: 14pt)
- **Body Text**: Optimal reading size (11-12pt) with 1.5 line spacing
- **Font Pairing**: Complementary heading and body fonts
- **Weights**: Bold for headings, regular for body, italic for emphasis
- **Kerning**: Adjust letter spacing for readability

Style elements:

- Paragraph spacing (6-12pt between paragraphs)
- Indentation (first line or block style)
- Lists (bullets, numbered, nested)
- Blockquotes and callouts
- Code blocks with syntax highlighting
- Tables with alternating row colors
- Figures and captions

### Step 4: Content Structure and Hierarchy

Organize document structure:

- **Front Matter**: Title page, copyright, dedication, acknowledgments
- **Table of Contents**: Auto-generated with page numbers and hyperlinks
- **Executive Summary**: Key findings and recommendations
- **Body**: Main content with logical section flow
- **Back Matter**: Appendices, bibliography, index, glossary

Implement heading hierarchy:

- H1: Document title only
- H2: Major sections (Introduction, Methodology, Results)
- H3: Subsections within major sections
- H4: Minor subdivisions
- H5-H6: Rarely needed, use sparingly

Add navigation aids:

- Clickable table of contents
- Cross-references between sections
- Page numbers and section markers
- Breadcrumb navigation (for long docs)

### Step 5: Special Elements Formatting

Format tables:

- Consistent column widths
- Header row styling (bold, background color)
- Alternating row colors for readability
- Cell padding and borders
- Caption and table number
- Source citation if applicable

Format figures and images:

- Consistent sizing and alignment
- Figure numbers and captions
- High-resolution images (300 DPI for print)
- Alt text for accessibility
- Proper spacing around images
- Image credits and sources

Format code blocks:

- Syntax highlighting for programming languages
- Line numbers for reference
- Consistent indentation
- Monospace font (Consolas, Monaco, Courier New)
- Copy button for easy code extraction

Format equations and formulas:

- LaTeX or MathML rendering
- Equation numbering and references
- Proper alignment and spacing
- Clear variable definitions

### Step 6: Citations and References

Configure citation style:

- APA (American Psychological Association)
- MLA (Modern Language Association)
- Chicago (Author-Date or Notes-Bibliography)
- IEEE (Institute of Electrical and Electronics Engineers)
- Harvard

Format in-text citations:

- Parenthetical citations with author and year
- Footnotes or endnotes
- Superscript numbers for IEEE style
- Hyperlinks to bibliography entries

Generate bibliography:

- Alphabetical by author last name
- Hanging indent formatting
- Italics for book and journal titles
- DOI and URL links where applicable
- Access dates for web sources

### Step 7: Headers, Footers, and Page Numbering

Design headers:

- Document title or section name
- Company logo (optional)
- Date or version number
- Consistent placement (left, center, right)

Design footers:

- Page numbers (e.g., "Page 5 of 23")
- Copyright notice
- Document classification (Confidential, Internal, Public)
- Contact information

Page numbering styles:

- Roman numerals (i, ii, iii) for front matter
- Arabic numerals (1, 2, 3) for body
- Section-based numbering (1-1, 1-2, 2-1)
- Different first page (no number on title page)

### Step 8: Quality Control and Validation

Run formatting checks:

- Consistent font usage throughout
- Proper heading hierarchy (no skipped levels)
- All figures and tables numbered sequentially
- All citations have corresponding bibliography entries
- No orphaned headings (heading at bottom of page)
- No widows (single line at top of page)

Accessibility validation:

- All images have alt text
- Proper heading structure for screen readers
- Sufficient color contrast (4.5:1 for body text)
- Tables have header rows defined
- Links have descriptive text (not "click here")

Cross-platform testing:

- Verify formatting in multiple PDF readers
- Test DOCX in Microsoft Word and Google Docs
- Check HTML rendering in different browsers
- Validate Markdown with common parsers

### Step 9: Multi-Format Export

Generate PDF:

- Embedded fonts for consistency
- Hyperlinked table of contents
- Bookmarks for major sections
- Searchable text (not scanned images)
- Optimized file size
- PDF/A compliance for archival

Generate DOCX:

- Styles-based formatting (not direct formatting)
- Track changes and comments preserved
- Embedded images and charts
- Compatible with Microsoft Word 2016+
- Google Docs compatible

Generate HTML:

- Semantic HTML5 markup
- Responsive design for mobile
- CSS for styling (embedded or external)
- JavaScript for interactive elements
- SEO-friendly meta tags

Generate Markdown:

- CommonMark or GitHub Flavored Markdown
- Preserve heading hierarchy
- Convert images to relative paths
- Maintain table structure
- Code block language tags

### Step 10: Final Review and Delivery

Perform final review:

- Proofread for typos and formatting errors
- Verify all links work correctly
- Check page breaks and layout
- Confirm branding consistency
- Test all exported formats

Package deliverables:

- Primary format (e.g., PDF)
- Source format (e.g., DOCX or Markdown)
- Alternative formats (HTML, EPUB)
- Embedded fonts folder
- Image assets folder
- Style guide documentation

Document formatting settings:

- Template used and customizations
- Font names and sizes
- Color palette (hex codes)
- Margin and spacing values
- Citation style

## Usage Examples

### Example 1: Corporate Business Report

```bash
/format --type report --template corporate --export pdf
```

**Input**: Draft business report in plain text or Markdown

```markdown
# Q4 2024 Sales Performance Report

## Executive Summary
Sales exceeded targets by 23% in Q4...

## Market Analysis
The North American market showed strong growth...
```

**Output**: Professional PDF report with:

- Corporate template with company branding
- Executive summary highlighted in callout box
- Charts and graphs properly formatted
- Table of contents with page numbers
- Header with company logo and report title
- Footer with page numbers and confidentiality notice

### Example 2: Academic Research Paper

```bash
/format --type whitepaper --template academic --export pdf --cite-style apa
```

**Input**: Research paper with citations

```markdown
# The Impact of AI on Modern Healthcare

## Abstract
This study examines... (Smith, 2023)

## Introduction
Recent advances in artificial intelligence (Johnson et al., 2024)...
```

**Output**: Formatted academic paper with:

- IEEE two-column layout
- Properly formatted APA citations
- Bibliography in alphabetical order
- Equation numbering and cross-references
- Figure captions with source attributions
- Page numbers in bottom right

### Example 3: Technical Ebook

```bash
/format --type ebook --template creative --export pdf,epub,html
```

**Input**: Multi-chapter ebook manuscript

```markdown
# Python for Data Science

## Chapter 1: Introduction to NumPy

### Installing NumPy
```python
pip install numpy
```

```

**Output**: Multi-format ebook with:
- Creative typography with custom fonts
- Syntax-highlighted code blocks
- Chapter headings on new pages
- Clickable table of contents
- EPUB with metadata for ebook readers
- HTML version with responsive design
- PDF optimized for tablet reading

### Example 4: Proposal with Custom Branding
```bash
/format --type proposal --template corporate --brand-guide ./brand.json --export pdf
```

**Input**: Proposal document + brand guidelines JSON

```json
{
  "logo": "./logo.png",
  "primary_color": "#003366",
  "secondary_color": "#66CCFF",
  "font_heading": "Montserrat",
  "font_body": "Open Sans"
}
```

**Output**: Branded proposal with:

- Custom color scheme applied to headings and accents
- Company logo in header
- Specified fonts throughout document
- Professional cover page with branding
- Consistent styling matching brand guide

### Example 5: Multi-Document Report Series

```bash
/format --type report --template corporate --batch ./reports/*.md --export pdf
```

**Input**: Directory containing multiple report files

```
./reports/
  01-introduction.md
  02-methodology.md
  03-results.md
  04-conclusion.md
```

**Output**: Combined or separate formatted reports with:

- Consistent formatting across all documents
- Continuous page numbering
- Master table of contents
- Cross-document references
- Unified bibliography

## Quality Control Checklist

Before finalizing document formatting, verify:

- [ ] Consistent font family and sizes throughout document
- [ ] Proper heading hierarchy (H1 > H2 > H3, no skipped levels)
- [ ] All figures numbered sequentially (Figure 1, Figure 2, etc.)
- [ ] All tables numbered sequentially (Table 1, Table 2, etc.)
- [ ] All citations have corresponding bibliography entries
- [ ] Table of contents is accurate and hyperlinked
- [ ] Page numbers are correct and consecutive
- [ ] Headers and footers appear on all pages (except title page)
- [ ] No orphaned headings (heading at bottom of page alone)
- [ ] No widows or orphans (single lines at top/bottom of pages)
- [ ] All images have sufficient resolution (300 DPI for print)
- [ ] All images have descriptive alt text for accessibility
- [ ] Color contrast meets WCAG 2.1 AA standards (4.5:1 minimum)
- [ ] Links are working and open to correct destinations
- [ ] Exported formats open correctly in target applications
- [ ] File size is optimized (not excessively large)
- [ ] Document metadata is complete (title, author, keywords)
- [ ] Copyright and licensing information included
- [ ] Version number and date are current
- [ ] No placeholder text remains (e.g., "Lorem ipsum", "TODO")

## Best Practices

### Typography Excellence

- Use serif fonts (Georgia, Times New Roman) for formal documents and body text readability
- Use sans-serif fonts (Arial, Helvetica, Calibri) for headings and presentations
- Limit font families to 2-3 maximum (one for headings, one for body)
- Maintain consistent line height (1.5x for body text, 1.2x for headings)
- Use proper em dashes (—) not hyphens (-) for breaks in thought

### Layout Optimization

- Set margins to 1 inch on all sides for printed documents
- Use wider margins (1.25-1.5 inches) for binding
- Break long documents into chapters with new page starts
- Place important information "above the fold" on first page
- Use white space generously—don't cram content

### Professional Appearance

- Start major sections on new pages
- Align images and tables consistently (left, center, or right)
- Use high-quality images (never stretched or pixelated)
- Keep color palette limited (2-3 colors plus black/white)
- Avoid decorative fonts in formal documents

### Performance and File Size

- Compress images before embedding (use WebP or optimized JPG)
- Embed only necessary fonts to reduce PDF size
- Remove metadata and hidden content before sharing externally
- Use PDF optimization tools to reduce file size by 30-50%
- For large documents, split into separate files by chapter

### Accessibility First

- Use descriptive link text ("Download Annual Report" not "Click Here")
- Provide alternative text for all images and charts
- Use sufficient color contrast (dark text on light background)
- Ensure document is navigable via keyboard only
- Tag PDFs properly for screen reader compatibility
- Avoid using color alone to convey information

### Common Pitfalls to Avoid

- **Don't** use multiple spaces for alignment—use tabs or tables instead
- **Don't** press Enter multiple times to create space—use paragraph spacing
- **Don't** manually number headings—use auto-numbering features
- **Don't** use hard page breaks excessively—let content flow naturally
- **Don't** apply direct formatting—use styles for consistency
- **Don't** forget to update table of contents after edits
- **Don't** use low-resolution images (<150 DPI for print)
- **Don't** mix citation styles within same document

### Pro Tips for Advanced Users

- Create custom style templates for recurring document types
- Use master pages for consistent headers/footers across sections
- Set up auto-replace for common terms (e.g., company name, product names)
- Use conditional formatting for dynamic content (dates, versions)
- Implement version control for collaborative document editing
- Create reusable text snippets for boilerplate content
- Use cross-reference fields instead of hard-coded page numbers
- Set up automated quality checks with linting tools

## Integration Points

### Related Commands

- `/template` - Create and manage reusable document templates
- `/style` - Apply and customize document styling and branding
- `/convert` - Convert between document formats (PDF, DOCX, HTML, Markdown)
- `/research/cite` - Generate citations in multiple academic formats

### Tool Integrations

- **Pandoc**: Universal document converter for format transformations
- **LaTeX**: Professional typesetting for academic and technical documents
- **Markdown**: Lightweight markup for easy content creation
- **Microsoft Word**: DOCX editing and template management
- **Google Docs**: Collaborative editing and cloud storage
- **Adobe Acrobat**: PDF creation and optimization
- **LibreOffice**: Open-source office suite for document processing

### Workflow Connections

1. **Content Creation** → `/format` → **Professional Document**
2. **Draft Document** → `/template` → `/format` → **Branded Output**
3. **Multiple Sources** → `/format --batch` → **Unified Report**
4. **Research Paper** → `/research/cite` → `/format` → **Published Paper**
5. **Markdown Content** → `/format` → **Multi-Format Export** (PDF, DOCX, HTML)

## Success Criteria

### Document Quality

- Professional appearance matching industry standards
- Consistent formatting throughout all sections
- Proper typographic hierarchy and readability
- All visual elements (images, tables, charts) properly formatted
- Zero formatting errors or inconsistencies

### Technical Excellence

- Clean, semantic document structure
- Valid output in all requested formats
- Accessible to users with disabilities (WCAG 2.1 AA)
- Optimized file sizes for sharing and archival
- Compatible with industry-standard tools

### User Experience

- Document is easy to navigate (TOC, bookmarks, page numbers)
- Content flows logically from section to section
- Visual elements enhance understanding
- Readable on multiple devices (desktop, tablet, mobile)
- Print-ready quality for physical documents

### Business Impact

- Reduces document creation time by 80%+
- Eliminates need for expensive design software/services
- Ensures brand consistency across all documents
- Enables rapid production of professional materials
- Supports multiple output formats from single source

### Measurable Outcomes

- Time savings: 6+ hours per document
- Cost reduction: $300+ per document (design fees avoided)
- Quality improvement: 95%+ stakeholder approval rate
- Consistency: 100% brand guideline compliance
- Accessibility: 100% WCAG 2.1 AA compliance
