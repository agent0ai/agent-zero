---
description: Convert documents between formats (PDF, DOCX, HTML, Markdown) while preserving formatting
argument-hint: [--from <format>] [--to <format>] [--input <file>] [--output <file>] [--preserve-styles]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Write, Bash
---

# Document Format Conversion Command

Convert documents between multiple formats (PDF, DOCX, HTML, Markdown, LaTeX, EPUB) while preserving formatting, styles, and structure.

## ROI: $15,000/year

- 90% faster format conversions (save 15 hours/month)
- Eliminate $5K/year in manual conversion costs
- Preserve formatting accuracy (95%+ fidelity)
- Batch convert 100+ documents simultaneously
- Support for 12+ file formats

## Key Benefits

- **Universal Conversion**: Convert between PDF, DOCX, HTML, Markdown, LaTeX, EPUB, RTF, ODT
- **Style Preservation**: Maintain fonts, colors, formatting across conversions
- **Batch Processing**: Convert hundreds of files with single command
- **Smart Mapping**: Intelligent format feature mapping
- **Quality Control**: Validation and comparison of source vs. output

## Implementation Steps

### Step 1: Format Detection and Analysis

Detect source document format:

- File extension analysis (.pdf, .docx, .html, .md, .tex, .epub)
- MIME type detection (application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document)
- Content signature verification (magic number checking)
- Encoding detection (UTF-8, ASCII, Latin-1, etc.)

Analyze source document structure:

- Document metadata (title, author, date, keywords)
- Content hierarchy (headings, sections, subsections)
- Special elements (tables, images, equations, code blocks)
- Styling information (fonts, colors, sizes, spacing)
- Embedded resources (images, fonts, stylesheets)
- Hyperlinks and cross-references

Identify conversion challenges:

- Format-specific features not supported in target format
- Complex layouts that may not translate well
- Embedded fonts that need substitution
- Images in incompatible formats
- Scripts or interactive elements
- Proprietary or encrypted content

### Step 2: Target Format Requirements

Define target format capabilities:

- **PDF**: Static layout, embedded fonts, images, hyperlinks, bookmarks
- **DOCX**: Styles, track changes, comments, embedded objects, fields
- **HTML**: Semantic markup, CSS styling, responsive design, hyperlinks
- **Markdown**: Plain text, basic formatting, code blocks, tables, images
- **LaTeX**: Academic typesetting, equations, bibliography, cross-references
- **EPUB**: Ebook format, reflowable text, table of contents, metadata

Map source features to target format:

```
Source: PDF → Target: DOCX
  ✓ Text content → Paragraphs
  ✓ Bold/italic → Character formatting
  ✓ Headings → Heading styles
  ✓ Images → Inline images
  ✓ Tables → Table objects
  ⚠ Embedded fonts → Font substitution
  ✗ Form fields → Not supported
  ✗ Signatures → Not supported
```

Configure conversion options:

- Preserve formatting (maximum fidelity)
- Simplify formatting (optimize for editability)
- Strip formatting (plain text only)
- Custom mapping rules
- Image handling (embed, link, extract)
- Font substitution rules

### Step 3: Pre-Conversion Processing

Clean and prepare source document:

- Remove hidden or metadata content (optional)
- Fix encoding issues (convert to UTF-8)
- Normalize line endings (CRLF → LF)
- Remove extraneous whitespace
- Fix broken links or references
- Validate document structure

Extract embedded resources:

- Images (extract to separate files or embed in output)
- Fonts (embed or substitute)
- Stylesheets (inline or external)
- Scripts (preserve, convert, or remove)
- Metadata (preserve in target format)

Optimize for conversion:

- Simplify complex layouts
- Flatten layers or groups
- Rasterize vector graphics if needed
- Convert unsupported image formats
- Remove or convert form fields
- Linearize PDF for better text extraction

### Step 4: Conversion Engine Selection

Choose appropriate conversion engine:

**Pandoc** (Universal document converter):

- Supports: Markdown, HTML, LaTeX, DOCX, EPUB, PDF (via LaTeX)
- Strengths: Excellent Markdown/HTML support, academic formats
- Limitations: Limited PDF-to-DOCX conversion

**LibreOffice** (Office suite converter):

- Supports: DOCX, ODT, PDF, RTF, HTML
- Strengths: Office format conversions, batch processing
- Limitations: Requires installation, slower for large batches

**pdftotext/pdftohtml** (PDF extraction):

- Supports: PDF → text, HTML, XML
- Strengths: Fast, accurate text extraction from PDF
- Limitations: Limited formatting preservation

**Aspose/Adobe APIs** (Commercial solutions):

- Supports: All major formats with high fidelity
- Strengths: Best format preservation, advanced features
- Limitations: Licensing costs, API rate limits

Select engine based on:

- Source and target formats
- Required fidelity level
- Batch size and performance needs
- Budget and licensing constraints
- Available infrastructure

### Step 5: Format-Specific Conversion Logic

**PDF → DOCX Conversion:**

1. Extract text with layout information
2. Identify headings, paragraphs, lists
3. Extract and embed images
4. Recreate tables
5. Apply styles based on font properties
6. Generate DOCX with styles
7. Validate against source

**DOCX → PDF Conversion:**

1. Open DOCX with style information
2. Embed fonts for consistency
3. Convert fields to static content
4. Generate bookmarks from headings
5. Create PDF with hyperlinks
6. Set PDF metadata
7. Optimize file size

**Markdown → HTML Conversion:**

1. Parse Markdown syntax
2. Convert to HTML elements
3. Apply CSS styling
4. Syntax highlight code blocks
5. Generate table of contents
6. Add responsive meta tags
7. Optimize for web

**HTML → Markdown Conversion:**

1. Parse HTML DOM structure
2. Convert semantic HTML to Markdown
3. Extract images and create references
4. Simplify complex HTML to basic Markdown
5. Preserve code blocks with language tags
6. Generate clean, readable Markdown

**PDF → Markdown Conversion:**

1. Extract text from PDF
2. Identify heading hierarchy
3. Detect lists and tables
4. Extract images to separate files
5. Create Markdown with image references
6. Format code blocks
7. Clean up extracted text

### Step 6: Style and Formatting Preservation

Preserve typography:

- Font families (with fallbacks)
- Font sizes and weights
- Text colors
- Line heights and spacing
- Text alignment
- Character formatting (bold, italic, underline)

Preserve layout:

- Page margins and orientation
- Column layouts
- Section breaks
- Headers and footers
- Page numbers
- Watermarks

Preserve document structure:

- Heading hierarchy
- Paragraph styles
- List formatting (bullets, numbering)
- Table structures
- Image positioning and sizing
- Caption formatting

Handle format limitations:

- Substitute unavailable fonts
- Approximate unsupported styles
- Convert complex layouts to simpler equivalents
- Flatten layers if needed
- Rasterize vector graphics when necessary
- Document conversion compromises

### Step 7: Image and Media Handling

Extract images from source:

- Identify all images in document
- Extract with original quality
- Convert to target-compatible formats
- Optimize file sizes (optional)
- Generate meaningful filenames

Embed or link images in target:

- **Embed**: Include images within document file
- **Link**: Reference external image files
- **Extract**: Save images separately, create references
- Choose based on target format and use case

Image format conversions:

- PNG → JPG (for smaller file sizes)
- JPG → PNG (for transparency)
- TIFF → PNG/JPG (web compatibility)
- BMP → PNG/JPG (modern formats)
- SVG → PNG (rasterize if needed)
- EPS → SVG/PNG (vector conversion)

Optimize images:

- Compress without visible quality loss
- Resize to appropriate dimensions
- Convert to web-optimized formats
- Remove EXIF metadata (optional)
- Generate responsive image variants

### Step 8: Table and Data Conversion

Convert table structures:

- HTML tables → Markdown tables
- PDF tables → DOCX tables
- Excel tables → HTML tables
- Preserve cell formatting (bold, colors)
- Maintain column alignment
- Handle merged cells

Handle complex tables:

- Nested tables (flatten if needed)
- Tables with images
- Tables with formulas
- Multi-page tables
- Rotated tables
- Tables with irregular structure

Data extraction from tables:

- Extract to CSV for data processing
- Convert to JSON for APIs
- Export to Excel for analysis
- Preserve data types (numbers, dates, currency)

### Step 9: Quality Validation and Comparison

Validate conversion output:

- Document opens successfully in target format
- No missing content (compare page/word counts)
- Images are present and positioned correctly
- Formatting is preserved (visual comparison)
- Links work and point to correct targets
- Table of contents is accurate

Compare source vs. output:

- Side-by-side visual comparison
- Text diff for content verification
- Style consistency check
- Image quality comparison
- Layout similarity assessment
- Generate comparison report

Handle conversion errors:

- Log warnings and errors
- Flag problematic sections
- Provide manual review list
- Suggest corrections
- Document known limitations

Quality metrics:

- Conversion success rate (% of documents converted)
- Formatting fidelity score (0-100%)
- Average processing time per document
- Error rate (% of failed conversions)
- User satisfaction score

### Step 10: Batch Processing and Automation

Configure batch conversion:

- Source directory with multiple files
- File type filter (*.pdf,*.docx, etc.)
- Target format(s) to generate
- Output directory structure
- Naming conventions
- Parallel processing settings

Process files in batch:

```
Input:
  documents/
    report1.pdf
    report2.pdf
    report3.pdf

Command:
  /convert --from pdf --to docx,html --input ./documents/*.pdf --output ./converted/

Output:
  converted/
    docx/
      report1.docx
      report2.docx
      report3.docx
    html/
      report1.html
      report2.html
      report3.html
```

Monitor batch progress:

- Real-time progress indicator (15 of 100 files)
- Estimated time remaining
- Success/failure counts
- Current file being processed
- Error log for failed conversions

Generate batch report:

- Total files processed
- Successful conversions
- Failed conversions with reasons
- Average processing time
- Total time elapsed
- Storage space used
- Next steps for failed files

## Usage Examples

### Example 1: Convert PDF to DOCX

```bash
/convert --from pdf --to docx --input ./annual-report.pdf --output ./annual-report.docx --preserve-styles
```

**Input**: PDF annual report (50 pages)
**Output**: Editable DOCX with:

- All text extracted and formatted
- Images embedded in correct positions
- Tables recreated as DOCX tables
- Headings styled with heading styles
- Hyperlinks preserved
- 95% formatting fidelity

### Example 2: Convert Markdown to HTML

```bash
/convert --from md --to html --input ./README.md --output ./index.html --css ./styles.css
```

**Input**: Markdown documentation
**Output**: Styled HTML with:

- Semantic HTML5 markup
- Syntax-highlighted code blocks
- Responsive CSS styling
- Table of contents from headings
- Linked images
- SEO-friendly meta tags

### Example 3: Batch Convert Documents

```bash
/convert --from docx --to pdf,html --input ./documents/*.docx --output ./converted/ --parallel 4
```

**Input**: 25 DOCX files
**Output**: 50 files total (25 PDFs + 25 HTMLs)

- All DOCX converted to PDF with embedded fonts
- All DOCX converted to HTML with CSS
- Processing time: 2 minutes (4 parallel threads)
- 100% success rate

### Example 4: Convert PDF to Markdown

```bash
/convert --from pdf --to md --input ./whitepaper.pdf --output ./whitepaper.md --extract-images ./images/
```

**Input**: Technical whitepaper PDF
**Output**: Clean Markdown with:

- Extracted text formatted as Markdown
- Heading hierarchy preserved
- Images extracted to ./images/ directory
- Image references in Markdown
- Tables converted to Markdown syntax
- Code blocks properly formatted

### Example 5: Convert with Custom Options

```bash
/convert --from html --to pdf --input ./webpage.html --output ./document.pdf --page-size A4 --margins "1in" --header "Company Name" --footer "Page %p of %P"
```

**Input**: HTML webpage
**Output**: Professional PDF with:

- A4 page size
- 1-inch margins on all sides
- Custom header with company name
- Custom footer with page numbers
- Hyperlinks preserved
- Print-optimized styling

## Quality Control Checklist

- [ ] Source document format correctly detected
- [ ] Target format is appropriate for use case
- [ ] Conversion engine selected is optimal
- [ ] All text content successfully extracted/preserved
- [ ] Heading hierarchy maintained
- [ ] Paragraph formatting preserved
- [ ] Character formatting (bold, italic, underline) intact
- [ ] Images extracted and embedded correctly
- [ ] Image quality is acceptable (not degraded)
- [ ] Tables converted accurately
- [ ] Table formatting and alignment preserved
- [ ] Hyperlinks work and point to correct targets
- [ ] Table of contents is accurate (if present)
- [ ] Page numbers are correct (if applicable)
- [ ] Headers and footers preserved (if applicable)
- [ ] Metadata (title, author, date) transferred
- [ ] File opens correctly in target application
- [ ] Visual appearance matches source (within format constraints)
- [ ] No missing content (compare page/word counts)
- [ ] Conversion completed within acceptable time

## Best Practices

### Choosing the Right Format

- **PDF**: Best for final distribution, printing, archival
- **DOCX**: Best for collaborative editing, office workflows
- **HTML**: Best for web publishing, online documentation
- **Markdown**: Best for version control, plain-text editing, GitHub
- **LaTeX**: Best for academic papers, complex equations
- **EPUB**: Best for ebooks, reflowable content

### Optimizing for Fidelity

- Start with highest quality source available
- Use lossless conversions when possible
- Test conversion with sample before batch processing
- Manually review critical documents after conversion
- Keep original source files as backup
- Document any known conversion limitations

### Performance Optimization

- Use batch processing for multiple files
- Enable parallel processing for faster conversion
- Compress images before conversion
- Remove unnecessary metadata and hidden content
- Use appropriate tools for each conversion type
- Cache frequently converted documents

### Handling Conversion Failures

- Review error logs to identify issues
- Try alternative conversion engines
- Simplify complex source documents
- Convert in stages (PDF → HTML → DOCX)
- Manually fix problematic sections
- Document workarounds for recurring issues

### Accessibility Considerations

- Ensure alt text for images is preserved/added
- Maintain heading hierarchy for screen readers
- Preserve semantic HTML in web conversions
- Tag PDFs for accessibility
- Test converted documents with screen readers
- Add missing accessibility metadata

### Common Pitfalls to Avoid

- **Don't** assume 100% perfect conversion—always review output
- **Don't** convert from lossy formats (e.g., PDF → DOCX) without checking quality
- **Don't** forget to preserve images during conversion
- **Don't** ignore warnings and errors from conversion tools
- **Don't** convert encrypted/protected documents without permission
- **Don't** delete source files until confirming successful conversion
- **Don't** use outdated conversion tools with poor fidelity

### Pro Tips for Advanced Users

- Chain multiple conversions for optimal results (PDF → HTML → Markdown)
- Use conversion APIs for automated workflows
- Build custom conversion pipelines for specific document types
- Create conversion presets for common scenarios
- Implement quality checks in automated pipelines
- Use OCR for scanned PDFs before conversion
- Leverage format-specific metadata for better conversions

## Integration Points

### Related Commands

- `/format` - Format converted documents with professional styling
- `/template` - Apply templates to converted documents
- `/style` - Apply branding to converted documents

### Tool Integrations

- **Pandoc**: Universal document converter (Markdown, HTML, LaTeX, DOCX, EPUB)
- **LibreOffice**: Office format conversions (DOCX, ODT, PDF, RTF)
- **wkhtmltopdf**: HTML to PDF conversion with web engine
- **pdftotext**: PDF text extraction
- **ImageMagick**: Image format conversion
- **Calibre**: Ebook format conversion (EPUB, MOBI, AZW3)

### Workflow Connections

1. **Source Doc** → `/convert --to docx` → **Editable DOCX**
2. **Markdown** → `/convert --to html` → `/style` → **Branded HTML**
3. **PDF** → `/convert --to md` → **Edit in Git** → `/convert --to pdf` → **Updated PDF**
4. **DOCX** → `/convert --to pdf` → **Final Distribution**
5. **Batch Convert** → `/convert --from docx --to pdf,html` → **Multi-Format Output**

## Success Criteria

### Conversion Quality

- 95%+ formatting fidelity for supported conversions
- 100% content preservation (no missing text/images)
- Accurate table and structure conversion
- Proper heading hierarchy maintenance
- Working hyperlinks and references

### Performance

- Single document conversion: < 30 seconds
- Batch conversion: 100 documents in < 10 minutes
- Parallel processing support for faster throughput
- Memory-efficient processing of large documents
- Graceful handling of errors and edge cases

### Usability

- Simple command-line interface
- Clear progress indicators for batch processing
- Helpful error messages with resolution suggestions
- Comprehensive format support (12+ formats)
- Flexible configuration options

### Business Impact

- 90% faster document format conversions
- Eliminate manual conversion costs ($5K+ savings/year)
- Enable automated document workflows
- Support multi-format publishing from single source
- Reduce format-related compatibility issues

### Measurable Outcomes

- Conversion time savings: 15 hours/month
- Cost reduction: $5K+/year (no manual conversion services)
- Success rate: 98%+ of conversions complete without errors
- User satisfaction: 90%+ with conversion quality
- Format coverage: Support for 12+ document formats
