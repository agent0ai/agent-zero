---
description: Create and manage reusable document templates for consistent formatting
argument-hint: [--create <template-name>] [--from <source-doc>] [--category <corporate|academic|creative>] [--export <path>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Write, Bash
---

# Document Template Management Command

Create, customize, and manage reusable document templates for consistent branding and rapid document production.

## ROI: $35,000/year

- 90% faster document creation with pre-built templates
- Eliminate $12K/year in design and formatting costs
- Ensure 100% brand consistency across all documents
- Reduce review cycles by 70% with pre-approved templates
- Enable non-designers to create professional documents

## Key Benefits

- **Template Library**: Build comprehensive library of 50+ reusable templates
- **Brand Consistency**: Enforce corporate style guides automatically
- **Rapid Deployment**: Create new documents in minutes, not hours
- **Version Control**: Track template changes and maintain template history
- **Customization**: Easily adapt templates for specific use cases

## Implementation Steps

### Step 1: Template Requirements Analysis

Identify template needs:

- Document types (reports, proposals, memos, letters, presentations)
- Frequency of use (daily, weekly, monthly, occasional)
- Target audiences (internal, external, executive, technical)
- Industry standards and compliance requirements
- Brand guidelines and style requirements

Analyze existing documents:

- Extract common patterns and structures
- Identify reusable components (headers, footers, cover pages)
- Document color schemes and typography
- Catalog frequently used sections
- Note special formatting requirements

Gather stakeholder input:

- Interview frequent document creators
- Review brand guidelines from marketing
- Consult legal on required disclaimers
- Get IT input on technical requirements
- Validate accessibility requirements

### Step 2: Template Design and Structure

Define template architecture:

- **Master Template**: Base template with core styling
- **Variant Templates**: Specialized versions for specific use cases
- **Component Library**: Reusable blocks (title pages, headers, footers)
- **Style Definitions**: Typography, colors, spacing rules
- **Layout Grids**: Column structures and alignment guides

Create style guide documentation:

- Font specifications (family, size, weight, line height)
- Color palette (primary, secondary, accent, neutrals)
- Spacing rules (margins, padding, line spacing)
- Layout guidelines (columns, grids, alignment)
- Image specifications (size, resolution, placement)

### Step 3: Typography and Branding Setup

Configure font hierarchy:

- **H1 (Title)**: 28-32pt, Bold, Brand Primary Color
- **H2 (Section)**: 22-24pt, Bold, Brand Primary/Black
- **H3 (Subsection)**: 18-20pt, Semi-Bold, Black
- **H4 (Minor Heading)**: 14-16pt, Bold, Black
- **Body Text**: 11-12pt, Regular, Dark Gray (#333333)
- **Caption**: 9-10pt, Regular, Medium Gray (#666666)

Define color system:

- **Primary**: Main brand color for headings and accents
- **Secondary**: Supporting brand color for callouts
- **Accent**: Highlight color for important information
- **Neutral Dark**: Text and borders (#333333)
- **Neutral Medium**: Secondary text (#666666)
- **Neutral Light**: Backgrounds and dividers (#EEEEEE)

Set up spacing system:

- **XS**: 4px, **SM**: 8px, **MD**: 16px
- **LG**: 24px, **XL**: 32px, **XXL**: 48px

### Step 4: Component Creation

Build reusable components:

**Cover Page Component:**

- Company logo and branding
- Document title and subtitle
- Author and date information
- Version and confidentiality classification

**Header Component:**

- Section title or document title
- Page numbers
- Logo or branding element

**Footer Component:**

- Copyright notice
- Page number (e.g., "Page 5 of 23")
- Document classification (Confidential, Internal, Public)

**Table of Contents Component:**

- Auto-generated from heading hierarchy
- Clickable links to sections
- Page numbers aligned right

### Step 5: Template Variables and Placeholders

Define variable system for dynamic content:

- Document metadata (title, author, date, version)
- Company information (name, logo, address, website)
- Document settings (confidentiality, type, department)
- Styling options (color scheme, template variant)

Create placeholder syntax:

- **Required fields**: {{field_name}} - Must be filled
- **Optional fields**: {{field_name?}} - Can be left empty
- **Default values**: {{field_name|default}} - Use default if not provided
- **Conditional blocks**: {{#if}}...{{/if}} - Show/hide sections
- **Loops**: {{#each}}...{{/each}} - Repeat sections

### Step 6: Template Validation and Testing

Validate template structure:

- All required variables are defined
- Placeholder syntax is correct
- Components are properly linked
- Styles are applied consistently
- Images and assets exist and are accessible

Test with sample data:

- Populate all placeholders with test data
- Verify typography renders correctly
- Confirm colors match brand guidelines
- Check layout consistency across pages
- Test page breaks and flow

Test across platforms:

- Microsoft Word (DOCX)
- Google Docs
- PDF readers (Adobe, Preview, Chrome)
- Web browsers (Chrome, Firefox, Safari)
- Mobile devices (iOS, Android)

### Step 7: Template Library Organization

Organize templates by category:

**Corporate Templates:**

- Business reports (quarterly, annual, project)
- Proposals (sales, grant, partnership)
- Memos and letters
- Presentations and pitch decks
- Policies and procedures

**Academic Templates:**

- Research papers (IEEE, APA, MLA)
- Theses and dissertations
- Lab reports and literature reviews
- Conference papers

**Creative Templates:**

- Ebooks and whitepapers
- Magazines and newsletters
- Portfolios and case studies
- Marketing materials

**Technical Templates:**

- API documentation
- User manuals
- Technical specifications
- Architecture documents

Implement version control:

- Track template changes over time
- Maintain changelog for each version
- Use semantic versioning (MAJOR.MINOR.PATCH)
- Archive deprecated templates

### Step 8: Template Customization System

Enable template customization:

- Override default colors with custom palette
- Replace logo and branding elements
- Adjust typography (font family, sizes)
- Modify page layout (margins, columns)
- Add/remove template sections
- Customize headers and footers

Create customization configuration:

- Base template selection
- Color scheme overrides
- Font family selections
- Layout preferences
- Component toggles (enable/disable sections)

### Step 9: Template Export and Distribution

Package template for distribution:

- README with usage instructions
- Main template file (markdown, DOCX, HTML)
- Configuration file (YAML or JSON)
- Style definitions (CSS)
- Reusable components
- Assets (logos, images, fonts)
- Example documents

Export in multiple formats:

- **Markdown**: Source format for editing
- **DOCX**: Microsoft Word template (.dotx)
- **HTML**: Web-based template
- **LaTeX**: Academic typesetting
- **JSON**: Configuration and metadata

### Step 10: Template Maintenance and Updates

Establish update schedule:

- **Quarterly**: Review templates for improvements
- **Semi-Annual**: Update for brand guideline changes
- **Annual**: Major version updates with new features
- **As-Needed**: Bug fixes and urgent updates

Track template usage:

- Monitor which templates are most/least used
- Collect user feedback and pain points
- Log error reports and issues
- Measure time savings metrics

Version upgrade process:

- Test new version thoroughly
- Document all changes in changelog
- Notify users of new version
- Provide migration guide for breaking changes
- Maintain backward compatibility when possible

## Usage Examples

### Example 1: Create Corporate Report Template

```bash
/template --create "Quarterly Report" --category corporate --from ./sample-q4-report.md
```

**Input**: Existing well-formatted quarterly report
**Output**: Reusable template with:

- Extracted structure and styling
- Placeholders for variable content
- Preserved formatting (fonts, colors, layout)
- Component library (cover page, data tables)

### Example 2: Create Academic Paper Template

```bash
/template --create "IEEE Research Paper" --category academic --cite-style ieee
```

**Output**: IEEE-compliant template with:

- Two-column layout
- IEEE citation style configured
- Abstract, keywords, introduction sections
- Figure and table numbering
- Author biography section

### Example 3: Customize Existing Template

```bash
/template --load "Corporate Report" --customize --colors ./brand-colors.json --logo ./new-logo.png
```

**Input**: Customization parameters (colors, logo)
**Output**: Customized template variant with:

- Updated color scheme throughout
- New logo in header and cover page
- Modified component styling
- Saved as new template variant

### Example 4: Export Template Library

```bash
/template --export-all --format docx,html --output ./template-library/
```

**Output**: Complete template library exported as DOCX and HTML files

### Example 5: Generate Document from Template

```bash
/template --use "Quarterly Report" --data ./q1-2025-data.json --output q1-2025-report.pdf
```

**Input**: Template + data JSON with all placeholder values
**Output**: Generated report with all placeholders filled

## Quality Control Checklist

- [ ] All required variables are documented
- [ ] Placeholder syntax is consistent throughout
- [ ] Default values provided for optional fields
- [ ] Typography follows brand guidelines
- [ ] Color palette matches brand specifications
- [ ] Logo and images are high resolution (300 DPI)
- [ ] Headers and footers properly configured
- [ ] Page numbering system works correctly
- [ ] Table of contents auto-generates accurately
- [ ] Cross-references and links work
- [ ] Template renders correctly in all target formats
- [ ] Works in Microsoft Word, Google Docs, and other platforms
- [ ] Meets accessibility standards (WCAG 2.1 AA)
- [ ] Template documentation is complete
- [ ] Usage examples are provided
- [ ] Changelog is up to date
- [ ] Version number follows semantic versioning
- [ ] Template files are organized logically
- [ ] All assets are included in package
- [ ] No broken links or missing references

## Best Practices

### Template Design Principles

- Keep templates simple and focused on single document type
- Use consistent naming conventions for variables
- Provide sensible defaults for all optional fields
- Design for flexibility—allow easy customization
- Follow "mobile-first" approach for responsive templates

### Variable Naming Conventions

- Use lowercase with underscores: company_name not CompanyName
- Be descriptive: author_full_name not just author
- Group related variables: company_name, company_logo, company_address
- Use prefixes for namespacing: meta_title, brand_primary_color

### Component Reusability

- Create self-contained components that work independently
- Avoid tight coupling between components
- Use standardized interfaces for component integration
- Version components separately from templates
- Test components in isolation before integration

### Version Management

- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Increment MAJOR for breaking changes
- Increment MINOR for new features (backward compatible)
- Increment PATCH for bug fixes
- Tag releases in version control
- Maintain detailed changelog

### Performance Optimization

- Optimize images before embedding (compress, resize)
- Use vector graphics (SVG) when possible for logos
- Minimize embedded fonts (include only used characters)
- Cache frequently accessed templates
- Lazy-load optional components

### Common Pitfalls to Avoid

- **Don't** hardcode values that should be variables
- **Don't** create overly complex templates with too many options
- **Don't** skip documentation—document everything
- **Don't** forget to test on target platforms
- **Don't** use deprecated formatting techniques
- **Don't** include sensitive data in template examples
- **Don't** break backward compatibility without major version bump

### Pro Tips for Advanced Users

- Create template inheritance hierarchies (base → specialized)
- Use template preprocessors for advanced logic
- Implement template linting for quality control
- Set up automated template testing in CI/CD
- Create template galleries with visual previews
- Build template wizard for guided customization
- Implement template analytics to track usage

## Integration Points

### Related Commands

- `/format` - Use templates to format documents
- `/style` - Apply styling and branding to templates
- `/convert` - Convert templates between formats

### Tool Integrations

- **Pandoc**: Template conversion and processing
- **Mustache/Handlebars**: Template variable substitution
- **YAML**: Template configuration and metadata
- **Git**: Version control for template management

### Workflow Connections

1. **Create Template** → `/template --create` → **Template Library**
2. **Customize Template** → `/template --customize` → **Branded Variant**
3. **Use Template** → `/template --use` → `/format` → **Final Document**
4. **Update Template** → `/template --update` → **New Version Released**
5. **Export Templates** → `/template --export-all` → **Shared Library**

## Success Criteria

### Template Quality

- Professional appearance matching industry standards
- Complete documentation with usage examples
- All variables properly defined and documented
- Consistent styling throughout template
- Works correctly in all target formats

### Usability

- Easy to customize without technical expertise
- Clear variable naming and documentation
- Helpful examples and defaults provided
- Quick to generate documents (< 1 minute)
- Minimal learning curve for new users

### Technical Excellence

- Valid syntax in all template formats
- Efficient rendering and processing
- Cross-platform compatibility
- Accessible output (WCAG 2.1 AA)
- Version controlled and maintained

### Business Impact

- Reduces document creation time by 90%
- Ensures 100% brand consistency
- Eliminates design costs ($12K+ savings/year)
- Enables non-designers to create professional documents
- Scales across organization (100+ users)

### Measurable Outcomes

- Template creation time: 2-4 hours per template
- Document generation time: < 5 minutes from template
- Cost savings: $300+ per document (design fees avoided)
- User satisfaction: 90%+ approval rating
- Adoption rate: 80%+ of documents use templates
