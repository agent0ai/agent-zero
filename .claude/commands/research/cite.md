---
description: Generate and manage citations and bibliographies
argument-hint: [--style <apa|mla|chicago|ieee|harvard>] [--format <inline|footnote|endnote>] [--source <file|doi|url|isbn>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Write, Bash
---

# Citation Manager Command

Professional citation generation and bibliography management for academic and professional research.

## ROI: $25,000/year

- Save 15 hours/month on citation formatting (60% time reduction)
- Eliminate $8,000/year in citation management software costs
- Reduce citation errors by 95% with auto-formatting
- Support 5+ major citation styles with instant switching
- Auto-fetch metadata from DOIs, ISBNs, and URLs
- Batch process 100+ citations in minutes

## Key Benefits

- **Multi-Style Support**: Generate citations in APA, MLA, Chicago, IEEE, Harvard, and Vancouver formats
- **Auto-Metadata Extraction**: Fetch complete citation details from DOI, ISBN, URL, or PMID
- **Intelligent Formatting**: Auto-format authors, titles, dates, and publishers according to style guide
- **In-Text Citations**: Generate parenthetical, narrative, footnote, or endnote citations
- **Bibliography Generation**: Create alphabetized, formatted reference lists with hanging indents
- **Cross-Reference Management**: Track and update citations throughout documents
- **Export Formats**: Output to BibTeX, RIS, EndNote, Zotero, and plain text
- **Batch Processing**: Handle hundreds of citations simultaneously with consistency checks

## Implementation Steps

### Step 1: Source Identification and Metadata Extraction

Identify citation sources from user input:

- **DOI (Digital Object Identifier)**: Query CrossRef API for complete metadata
- **ISBN**: Fetch book information from Google Books or Open Library APIs
- **PMID (PubMed ID)**: Retrieve medical/scientific article data from PubMed
- **URL**: Extract metadata from webpage headers, Open Graph tags, or JSON-LD
- **Arxiv ID**: Get preprint information from Arxiv API
- **Manual Entry**: Parse user-provided citation details

Extract comprehensive metadata:

- Author(s): Full names, order, affiliations
- Title: Article/book title with proper capitalization
- Publication: Journal, publisher, or website name
- Date: Publication date (year, month, day where available)
- Volume/Issue: For journal articles
- Pages: Page range or article number
- DOI/URL: Permanent identifiers
- Edition: For books (1st, 2nd, revised, etc.)
- Access Date: For online sources
- Publisher Location: City and state/country

Validate metadata completeness:

- Flag missing required fields (author, title, year)
- Suggest corrections for malformed data
- Verify DOI format (10.XXXX/...)
- Check ISBN checksums
- Validate URL accessibility

### Step 2: Citation Style Selection and Configuration

Support major citation styles with complete formatting rules:

**APA (American Psychological Association) 7th Edition**:

- Author-date parenthetical citations: (Smith, 2024)
- Multiple authors: (Smith & Jones, 2024) or (Smith et al., 2024)
- Reference list: Hanging indent, alphabetical by author surname
- Title case: Sentence case for article titles, title case for journal names
- Special rules: DOIs, retrieval dates for web sources

**MLA (Modern Language Association) 9th Edition**:

- Author-page parenthetical citations: (Smith 45)
- Works Cited: Hanging indent, alphabetical
- Title formatting: "Article titles" in quotes, *Book Titles* in italics
- Container concept: Journal/website as container
- No URLs unless no other identifier exists

**Chicago Manual of Style 17th Edition**:

- Notes-Bibliography: Footnotes with full citation on first mention
- Author-Date: Similar to APA with different formatting
- Bibliography: Alphabetical with hanging indent
- Special punctuation and abbreviation rules

**IEEE (Institute of Electrical and Electronics Engineers)**:

- Numbered citations: [1], [2], [3]
- References: Numbered list in order of first appearance
- Author format: Initials before surname
- Abbreviated journal names

**Harvard Referencing**:

- Author-date: (Smith 2024, p. 45)
- Reference list: Alphabetical with hanging indent
- Multiple works: (Smith 2024a, 2024b)

**Vancouver Style** (Medical/Scientific):

- Numbered citations in order of appearance
- Abbreviated journal names per Index Medicus
- Author limit: List first 6 authors, then "et al."

Configure style-specific options:

- Date format: (2024), (2024, March 15), or March 15, 2024
- Author separator: "&" vs "and" vs commas
- Title capitalization rules
- Italics vs quotation marks
- Abbreviation standards
- Punctuation preferences

### Step 3: Author Name Formatting

Parse and format author names according to citation style:

Author name parsing:

- Detect name format: "First Last", "Last, First", "Last, F."
- Handle prefixes: van, de, von, della, etc.
- Manage suffixes: Jr., Sr., III, PhD, MD
- Identify organization authors: WHO, NASA, etc.
- Parse multiple authors with various separators

Style-specific formatting:

- **APA**: Last, F. M. (initials with periods)
- **MLA**: Last, First Middle.
- **Chicago**: Last, First M.
- **IEEE**: F. M. Last (initials first)
- **Harvard**: Last, F.M. (no spaces between initials)

Author list handling:

- Single author: Standard format
- Two authors: Smith & Jones or Smith and Jones
- Three or more: List all vs "et al." cutoff
- Organization authors: Full name without inversion
- Anonymous works: Begin with title
- Editors vs authors: Add "(Ed.)" or "(Eds.)"

Special cases:

- Non-English names: Preserve original format
- Mononyms: Single name handling
- Corporate authors: No inversion
- Multiple roles: Author/editor combinations

### Step 4: Title and Publication Formatting

Format titles according to style guidelines:

Title capitalization:

- **Sentence case**: Only first word and proper nouns capitalized
- **Title Case**: All Major Words Capitalized
- **Preserve original**: For non-English titles
- Subtitle handling: Colon separation with proper capitalization

Title styling:

- Article titles: "In quotation marks" or plain text
- Book titles: *Italicized* or underlined
- Journal titles: *Italicized* with proper abbreviations
- Webpage titles: "In quotes" or plain
- Conference papers: Special formatting per style

Publication information formatting:

- Journal: *Journal Name*, Volume(Issue), pages
- Book: City, State: Publisher
- Website: Site Name, URL, access date
- Report: Organization, report number
- Thesis/Dissertation: University, degree type

Special formatting rules:

- Volume numbers: Bold, italic, or plain per style
- Issue numbers: In parentheses after volume
- Page ranges: Use en-dash (45-67 not 45-67)
- DOI formatting: <https://doi.org/10.XXXX> or just doi:10.XXXX
- URL formatting: Remove hyperlinks in print versions

### Step 5: In-Text Citation Generation

Generate citations for insertion into document text:

**Parenthetical citations**:

- Basic: (Smith, 2024)
- With page: (Smith, 2024, p. 45) or (Smith 2024:45)
- Multiple works: (Smith, 2024; Jones, 2023)
- Same author, same year: (Smith, 2024a, 2024b)

**Narrative citations**:

- APA: Smith (2024) argues that...
- MLA: Smith argues that... (45)
- Chicago: Smith states...¹

**Footnote/Endnote citations**:

- Full citation on first mention
- Shortened form for subsequent references
- Ibid. for consecutive same-source citations
- Op. cit. for non-consecutive same-source

**Numbered citations**:

- IEEE: Text goes here [1, 2].
- Vancouver: Text here.¹,²
- Sequential numbering in order of appearance

Special citation scenarios:

- Secondary sources: (Smith, as cited in Jones, 2024)
- No date: (Smith, n.d.)
- No author: (Title, 2024)
- Personal communication: (J. Smith, personal communication, March 2024)
- Multiple authors by same name: (J. Smith vs R. Smith)

### Step 6: Bibliography/Reference List Generation

Create formatted reference list with all cited works:

Alphabetization rules:

- By author surname (Last, First)
- Organization names alphabetized by first significant word
- Anonymous works by title
- Same author: Chronological (oldest first)
- Same author, same year: Use 2024a, 2024b notation

Formatting specifications:

- Hanging indent: First line flush, subsequent lines indented
- Single or double spacing per style requirements
- Alphabetical or numbered order
- Separate sections for different source types (optional)

Entry formatting by source type:

**Journal Articles**:

- APA: Author, A. A. (2024). Article title. *Journal Name*, *Volume*(Issue), pages. <https://doi.org/10.XXXX>
- MLA: Author, First. "Article Title." *Journal Name*, vol. X, no. Y, 2024, pp. XX-YY.
- Chicago: Author, First Last. "Article Title." *Journal Name* Volume, no. Issue (2024): pages.

**Books**:

- APA: Author, A. A. (2024). *Book title: Subtitle* (2nd ed.). Publisher.
- MLA: Author, First. *Book Title: Subtitle*. Publisher, 2024.
- IEEE: F. M. Author, *Book Title*, Edition. City, State: Publisher, 2024.

**Websites**:

- APA: Author, A. A. (2024, Month Day). Page title. *Site Name*. URL
- MLA: Author. "Page Title." *Website Name*, Publisher, Date, URL.

**Edited Books/Chapters**:

- Chapter author, chapter title, "In" book editor, book title, pages, publisher

Quality control:

- Verify all in-text citations have bibliography entries
- Check for duplicate entries
- Ensure consistent formatting throughout
- Validate all DOIs and URLs
- Remove citations no longer referenced in text

### Step 7: Cross-Reference Management and Updates

Track citations throughout documents and maintain consistency:

Citation tracking:

- Assign unique IDs to each source
- Map in-text citations to bibliography entries
- Track citation frequency and locations
- Identify uncited bibliography entries

Cross-reference synchronization:

- Update in-text citations when bibliography changes
- Renumber citations when sources added/removed
- Update page numbers and years
- Maintain alphabetical order in bibliography

Change management:

- Track citation edits and history
- Highlight citations needing verification
- Flag broken DOI/URL links
- Alert to style inconsistencies

Document scanning:

- Parse document for all citations
- Extract cited sources automatically
- Identify citation format (parenthetical, footnote, etc.)
- Generate missing bibliography entries

### Step 8: Export and Integration

Export citations to multiple formats for use in other tools:

**BibTeX Export**:

```bibtex
@article{smith2024,
  author = {Smith, John A. and Jones, Mary B.},
  title = {Article Title Here},
  journal = {Journal Name},
  year = {2024},
  volume = {45},
  number = {3},
  pages = {123--145},
  doi = {10.1234/example}
}
```

**RIS Export** (RefMan, EndNote, Zotero):

```
TY  - JOUR
AU  - Smith, John A.
AU  - Jones, Mary B.
TI  - Article Title Here
JO  - Journal Name
PY  - 2024
VL  - 45
IS  - 3
SP  - 123
EP  - 145
DO  - 10.1234/example
ER  -
```

**JSON Export** (Citeproc):

```json
{
  "type": "article-journal",
  "author": [{"family": "Smith", "given": "John A."}],
  "title": "Article Title",
  "container-title": "Journal Name",
  "issued": {"date-parts": [[2024]]},
  "volume": "45",
  "issue": "3",
  "page": "123-145",
  "DOI": "10.1234/example"
}
```

Integration with reference managers:

- Zotero: Import/export via BibTeX or RIS
- Mendeley: RIS format or CSV
- EndNote: RIS or XML format
- RefWorks: RIS format
- LaTeX/BibTeX: Native .bib files

Word processor integration:

- Microsoft Word: XML bibliography format
- Google Docs: Formatted text with citations
- LibreOffice: RIS import
- LaTeX: BibTeX .bib files

### Step 9: Batch Processing and Automation

Handle multiple citations efficiently with automation:

Batch import:

- Import DOI lists (one per line)
- Import BibTeX/RIS files
- Parse reference lists from PDFs
- Extract citations from existing documents

Bulk operations:

- Convert citation style for entire bibliography
- Update all metadata from online sources
- Validate all DOIs and URLs
- Check for duplicate entries
- Standardize author name formats

Automated workflows:

- Watch folder for new papers → auto-generate citations
- PDF import → extract metadata → create citation
- DOI list → fetch metadata → generate bibliography
- Style conversion: APA → MLA → Chicago with one command

Quality assurance automation:

- Auto-check citation completeness (all required fields)
- Validate formatting consistency
- Check for style guideline compliance
- Identify potential duplicates
- Flag outdated URLs (404 errors)

### Step 10: Validation and Quality Control

Ensure citations meet academic standards and style requirements:

Format validation:

- Author names properly formatted per style
- Titles correctly capitalized and styled
- Dates in correct format
- Page numbers use en-dash not hyphen
- DOIs formatted correctly
- URLs are valid and accessible

Completeness checks:

- All required fields present for source type
- No placeholder text (e.g., "Author", "Title")
- Publication dates are reasonable (not future)
- Volume/issue numbers present for journals
- Publisher and location for books

Consistency verification:

- Same style applied throughout
- Consistent author name format
- Consistent date format
- Consistent abbreviation use
- Matching in-text and bibliography entries

Style guideline compliance:

- APA: Ampersand in parenthetical, "and" in narrative
- MLA: No comma before page number
- Chicago: Correct punctuation in footnotes
- IEEE: Abbreviated journal names
- Harvard: Consistent use of "pp." for pages

Error detection:

- Duplicate citations (same work cited twice)
- Orphaned citations (in text but not in bibliography)
- Missing citations (in bibliography but not in text)
- Formatting inconsistencies
- Invalid characters or encoding issues

## Usage Examples

### Example 1: Generate APA Citation from DOI

```bash
/research/cite --style apa --source doi:10.1038/s41586-024-07146-0
```

**Input**: DOI identifier

```
10.1038/s41586-024-07146-0
```

**Output**: Complete APA citation

```
In-text citation:
(Anderson et al., 2024)

Bibliography entry:
Anderson, J. R., Smith, M. K., Chen, L., & Patel, S. (2024).
    Machine learning applications in climate prediction.
    Nature, 625(7993), 234-242.
    https://doi.org/10.1038/s41586-024-07146-0
```

### Example 2: Convert Bibliography from APA to MLA

```bash
/research/cite --style mla --convert-from apa --file references.txt
```

**Input**: APA-formatted bibliography

```
Smith, J. A. (2024). *Understanding neural networks*. MIT Press.

Jones, M. B., & Davis, R. K. (2023). Deep learning fundamentals.
    *Journal of AI Research*, 45(2), 123-145.
```

**Output**: MLA-formatted bibliography

```
Smith, John A. *Understanding Neural Networks*. MIT Press, 2024.

Jones, Mary B., and Robert K. Davis. "Deep Learning Fundamentals."
    *Journal of AI Research*, vol. 45, no. 2, 2023, pp. 123-145.
```

### Example 3: Batch Process DOI List

```bash
/research/cite --style ieee --batch --source doi-list.txt
```

**Input**: File with multiple DOIs

```
10.1109/CVPR.2024.12345
10.1145/3548606.3560635
10.1038/nature12345
```

**Output**: IEEE-formatted reference list

```
[1] J. Smith, M. Johnson, and R. Davis, "Attention mechanisms in
    transformer models," in Proc. IEEE Conf. Computer Vision and
    Pattern Recognition (CVPR), 2024, pp. 1234-1242.

[2] A. Chen and L. Wang, "Federated learning for privacy preservation,"
    in Proc. ACM Conf. Computing Machinery, vol. 15, 2023, pp. 45-58.

[3] S. Patel et al., "CRISPR applications in gene therapy,"
    Nature, vol. 589, pp. 234-239, Jan. 2024.
```

### Example 4: Generate Footnote Citations for Chicago Style

```bash
/research/cite --style chicago --format footnote --inline
```

**Input**: In-text citation request

```
Quote from Smith's book on page 67
```

**Output**: Formatted footnote

```
Footnote text:
¹ John A. Smith, *Understanding Neural Networks*
  (Cambridge, MA: MIT Press, 2024), 67.

Subsequent references:
² Smith, *Neural Networks*, 72.

³ Ibid., 73.
```

### Example 5: Create Citation from Webpage with Auto-Metadata

```bash
/research/cite --style apa --source url:https://example.com/article
```

**Input**: URL to article

```
https://www.scientificamerican.com/article/quantum-computing-breakthrough/
```

**Output**: APA citation with auto-extracted metadata

```
In-text citation:
(Johnson, 2024)

Bibliography entry:
Johnson, T. (2024, March 15). Quantum computing breakthrough enables
    faster drug discovery. *Scientific American*.
    https://www.scientificamerican.com/article/quantum-computing-breakthrough/
```

### Example 6: Generate BibTeX for LaTeX Document

```bash
/research/cite --export bibtex --file my-sources.json
```

**Input**: JSON with multiple sources

```json
[
  {
    "type": "article",
    "author": "Smith, J. A.",
    "title": "Machine Learning Methods",
    "journal": "AI Journal",
    "year": 2024,
    "volume": 15,
    "pages": "45-67"
  }
]
```

**Output**: BibTeX file

```bibtex
@article{smith2024machine,
  author = {Smith, John A.},
  title = {Machine Learning Methods},
  journal = {AI Journal},
  year = {2024},
  volume = {15},
  pages = {45--67}
}
```

### Example 7: Scan Document and Generate Bibliography

```bash
/research/cite --scan paper.md --style mla --generate-bibliography
```

**Input**: Document with in-text citations

```markdown
Recent studies (Smith 2024; Jones 2023) have shown...
According to Chen (2024), the results indicate...
```

**Output**: Complete MLA Works Cited

```
Works Cited

Chen, Maria. "Deep Learning Applications." *Tech Review*,
    vol. 12, 2024, pp. 34-56.

Jones, Robert. "Neural Network Fundamentals." *AI Quarterly*,
    vol. 8, no. 2, 2023, pp. 123-145.

Smith, John. *Machine Learning Theory*. MIT Press, 2024.
```

## Quality Control Checklist

Before finalizing citations, verify:

- [ ] All author names formatted correctly for chosen style
- [ ] Titles use proper capitalization (sentence case vs title case)
- [ ] Journal/book titles italicized or formatted per style
- [ ] Publication dates in correct format (2024 vs 2024, March)
- [ ] Volume and issue numbers present for journal articles
- [ ] Page ranges use en-dash (–) not hyphen (-)
- [ ] DOIs formatted correctly with <https://doi.org/> prefix
- [ ] URLs are valid and accessible (no 404 errors)
- [ ] All in-text citations have corresponding bibliography entries
- [ ] No duplicate entries in bibliography
- [ ] Bibliography alphabetized correctly by author surname
- [ ] Hanging indent applied to bibliography entries
- [ ] Ampersand (&) vs "and" used correctly per style
- [ ] "et al." applied consistently after correct author count
- [ ] Abbreviations match style guide (pp., vol., no., ed.)
- [ ] Special characters and accents preserved in non-English names
- [ ] Access dates included for web sources where required
- [ ] Publisher location included for books where required
- [ ] Edition numbers included for books (2nd ed., Rev. ed.)
- [ ] No placeholder text remains (Author, Title, Year)

## Best Practices

### Citation Accuracy

- **Always verify auto-generated citations** against the original source, especially for complex sources like edited volumes or conference proceedings
- **Double-check author names** for correct spelling, initials, and order - errors here are immediately visible to reviewers
- **Verify publication dates** match the actual publication, not submission or online posting dates
- **Check page numbers** are accurate ranges, especially for chapters in edited books
- Use **persistent identifiers** (DOI, PMID) whenever available instead of unstable URLs
- For **preprints**, note the version and date, as content may change before final publication

### Style Guide Adherence

- **Choose one citation style** and use it consistently throughout the entire document
- **Consult the latest edition** of style manuals (APA 7th, MLA 9th, Chicago 17th) as rules change between editions
- **Follow discipline conventions**: APA for social sciences, MLA for humanities, IEEE for engineering, Vancouver for medicine
- For **ambiguous cases**, check the style guide's official examples or FAQs
- **Note style variations** in your field - some journals have custom citation requirements
- Keep a **style guide reference** handy for quick lookups of special cases

### Metadata Management

- **Fetch metadata early** in your research process to avoid last-minute citation scrambles
- **Store complete metadata** even if not all fields are used in citations - better to have too much information
- **Organize citations** by project or topic using tags or folders
- **Back up citation libraries** regularly - losing citation data wastes hours of work
- Use **citation managers** (Zotero, Mendeley) to sync across devices and share with collaborators
- **Export citations** in multiple formats (BibTeX, RIS, JSON) for flexibility

### Common Mistakes to Avoid

- **Don't mix citation styles** within a document (e.g., APA for some, MLA for others)
- **Don't use "Retrieved from"** in APA 7th unless the source is likely to change over time
- **Don't include database names** in most citations unless specifically required by style
- **Don't assume auto-generated citations are perfect** - always review for accuracy
- **Don't forget to update citations** when sources are published (e.g., preprints to journal articles)
- **Don't cite Wikipedia** in academic work - use the original sources it references instead
- **Don't over-cite** common knowledge or your own previously published work without disclosure

### Efficiency Tips

- **Use keyboard shortcuts** or commands for inserting citations during writing
- **Create citation templates** for frequently used source types in your field
- **Batch import** DOIs at the end of reading sessions rather than one at a time
- **Set up auto-backup** of citation library to cloud storage
- **Learn BibTeX keys** naming conventions for easy LaTeX integration (author-year-keyword)
- **Use citation picker** plugins for word processors to insert citations without leaving your document
- **Maintain a reading list** separate from cited works to track sources for future use

### Advanced Techniques

- **Create custom citation styles** using CSL (Citation Style Language) for non-standard requirements
- **Use regex patterns** to batch-edit citation fields across multiple entries
- **Set up automated workflows** to monitor DOIs for metadata updates or corrections
- **Integrate with writing tools** (Overleaf, Scrivener, Obsidian) for seamless citation insertion
- **Track citation metrics** for your own publications using Google Scholar, Scopus, or Web of Science
- **Use citation mapping** tools to visualize connections between sources and identify key papers
- **Implement version control** for citation libraries when collaborating on research projects

### Ethical Considerations

- **Cite all sources** that contributed to your work, even if not directly quoted
- **Avoid citation bias** - don't only cite sources that support your argument
- **Give credit properly** for ideas, methods, and data, even from informal sources
- **Update retracted papers** citations with appropriate notices
- **Distinguish between** primary sources and secondary discussions of those sources
- **Acknowledge** both supporting and contradicting research fairly

## Integration Points

### Related Commands

- `/research/gather` - Collect research sources with automatic citation extraction
- `/research/annotate` - Add notes to sources while preserving citation metadata
- `/research/organize` - Organize cited sources into knowledge base structure
- `/docs/format` - Format final document with properly styled citations and bibliography

### Tool Integrations

- **Zotero**: Import/export citations, sync libraries, browser integration
- **Mendeley**: Reference management with PDF annotation and citation insertion
- **EndNote**: Desktop citation manager for Windows/Mac
- **BibTeX**: LaTeX citation management for academic publishing
- **CrossRef API**: Fetch metadata from DOIs automatically
- **PubMed API**: Retrieve medical/scientific article information
- **Google Scholar**: Search and extract citation information
- **ORCID**: Link author identifiers for disambiguation

### Workflow Connections

1. **Research** → `/research/gather` → `/research/cite` → **Formatted Bibliography**
2. **DOI List** → `/research/cite --batch` → **Complete Reference List**
3. **Draft Document** → `/research/cite --scan` → **Auto-Generated Citations**
4. **Citation Library** → `/research/cite --export` → **BibTeX/RIS Export** → LaTeX/Zotero
5. **APA Format** → `/research/cite --convert` → **MLA Format** → Style Switch

## Advanced Features

### Custom Citation Styles

Create organization-specific or journal-specific citation formats:

- Define custom field requirements
- Specify unique formatting rules
- Set abbreviation standards
- Configure punctuation preferences
- Save as reusable style template

### Citation Network Analysis

Visualize relationships between cited works:

- Identify most-cited sources
- Find citation clusters and themes
- Discover missing key papers
- Track citation chronology
- Generate citation maps

### Collaborative Citation Management

Share citation libraries with team members:

- Sync shared libraries across devices
- Track who added which citations
- Resolve duplicate entries
- Merge citation libraries
- Export team bibliography

### Smart Citation Suggestions

AI-powered citation recommendations:

- Suggest related sources based on current citations
- Identify gaps in literature review
- Recommend recent publications in field
- Find highly-cited works you may have missed
- Alert to retracted or corrected papers

## Common Use Cases

### Academic Research Paper

Use case: Doctoral student writing dissertation with 200+ sources
Solution: Batch import DOIs → generate APA citations → scan chapters → validate completeness

### Literature Review

Use case: Systematic review requiring 100+ article citations in Vancouver style
Solution: PubMed PMID list → auto-fetch metadata → generate numbered citations → export to EndNote

### Grant Proposal

Use case: Research proposal needing 50 citations in Chicago author-date style
Solution: Import from Zotero → convert to Chicago → generate bibliography → update in-text citations

### Conference Paper

Use case: IEEE conference paper with strict citation format requirements
Solution: Import BibTeX → validate IEEE style → abbreviate journal names → export formatted references

### Book Chapter

Use case: Contributing author needs consistent citations with other chapters
Solution: Receive style guide → set custom rules → generate citations → validate against examples

### Blog Post with Academic Sources

Use case: Science writer citing academic papers for general audience
Solution: Simplify citations for readability → include hyperlinks → generate "Further Reading" list

### Thesis Format Conversion

Use case: Converting master's thesis from MLA to APA for journal submission
Solution: Scan document → extract all citations → batch convert to APA → regenerate bibliography

### Multi-Document Research Project

Use case: Multiple papers citing overlapping sources
Solution: Maintain master citation library → export subsets per paper → ensure consistency

### Fact-Checking Article

Use case: Journalist verifying sources and providing citations
Solution: URL import → auto-extract metadata → generate web citations → include access dates

### Legal Brief

Use case: Attorney citing case law and legal documents
Solution: Use legal citation format → Bluebook style → case name formatting → court and year

## Troubleshooting

### DOI Not Found

**Problem**: DOI returns no metadata or error
**Solutions**:

- Verify DOI format is correct (10.XXXX/...)
- Try alternative databases (PubMed, Google Scholar)
- Check if DOI is newly registered (24-48 hour delay)
- Manually enter citation if metadata unavailable
- Use PMID or other identifier instead

### Incorrect Metadata

**Problem**: Auto-fetched citation has wrong authors or title
**Solutions**:

- Verify against the actual publication
- Check if fetching from correct source (preprint vs final)
- Manually edit incorrect fields
- Report errors to CrossRef or source database
- Use different identifier (DOI vs PMID) for better metadata

### Style Formatting Errors

**Problem**: Generated citations don't match style guide examples
**Solutions**:

- Verify using latest edition of style manual
- Check for field-specific variations
- Review special cases (no author, no date, etc.)
- Consult style guide's official FAQ
- Test with known-correct example

### Duplicate Detection Issues

**Problem**: Same source appears multiple times in bibliography
**Solutions**:

- Run duplicate detection algorithm
- Check for variations in author names
- Look for different DOIs (preprint vs published)
- Merge duplicate entries manually
- Standardize citation keys

### Export Format Problems

**Problem**: Exported citations don't import correctly to reference manager
**Solutions**:

- Verify export format matches import expectations
- Check file encoding (UTF-8 vs ASCII)
- Test with small sample before bulk export
- Update reference manager software
- Try alternative export format (RIS vs BibTeX)

## Success Criteria

### Citation Accuracy

- 100% of citations have all required fields for the chosen style
- Zero formatting errors in author names, titles, or publication details
- All DOIs and URLs validated and accessible
- Dates formatted consistently throughout
- Special characters and accents preserved correctly

### Style Compliance

- Citations match official style guide examples exactly
- Consistent formatting applied to all entry types
- Proper use of italics, quotation marks, and punctuation
- Abbreviations follow style standards
- In-text citations match bibliography format

### Efficiency Metrics

- Citation generation time: < 30 seconds per source
- Batch processing: 100+ citations in < 5 minutes
- Metadata accuracy: 95%+ from auto-fetch
- Manual corrections needed: < 10% of citations
- Export/import success rate: 100%

### User Experience

- Citations readable and properly formatted
- Bibliography easy to navigate and search
- Clear error messages for validation issues
- Intuitive style switching without data loss
- Seamless integration with writing workflow

### Quality Assurance

- Zero orphaned citations (cited but not in bibliography)
- Zero missing citations (in bibliography but not cited)
- No duplicate entries
- All placeholders replaced with real data
- Style consistency score: 100%
